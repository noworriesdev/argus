def get_messages(tx):
    logging.info("Fetching messages from the database...")
    messages = tx.run(
        "MATCH (m:Message) RETURN m.id AS id, m.content AS content"
    ).data()
    logging.info(f"Fetched {len(messages)} messages from the database.")
    return messages


def calculate_sentiment_and_save(messages):
    logging.info("Calculating sentiment scores...")
    sentiment_data = []
    for idx, message in enumerate(messages, start=1):
        content = message["content"]
        message_id = message["id"]
        sentiment = analyzer.polarity_scores(content)
        sentiment_data.append(
            {
                "message_id": message_id,
                "positive": sentiment["pos"],
                "neutral": sentiment["neu"],
                "negative": sentiment["neg"],
                "compound": sentiment["compound"],
            }
        )
        if idx % 100 == 0:  # Log every 100 messages processed
            logging.info(f"Processed {idx} messages...")

    logging.info("Writing sentiment data to JSON file...")
    with open("./sentiment_data.json", "w") as f:
        json.dump(sentiment_data, f)


def update_sentiments_with_apoc(tx):
    logging.info("Updating sentiments in the database using APOC...")
    return tx.run(
        """
        CALL apoc.periodic.iterate(
            "CALL apoc.load.json('file:///./sentiment_data.json') YIELD value RETURN value",
            "MATCH (m:Message {id: value.message_id}) "
            "SET m.positive = value.positive, "
            "    m.neutral = value.neutral, "
            "    m.negative = value.negative, "
            "    m.compound = value.compound",
            {batchSize: 100, iterateList: true, parallel: true}
        ) YIELD batches, total, errorMessages
        RETURN batches, total, errorMessages
    """
    ).single()


if __name__ == "__main__":
    import json
    import logging
    from neo4j import GraphDatabase
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    analyzer = SentimentIntensityAnalyzer()

    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
    try:
        with driver.session() as session:
            # messages = session.read_transaction(get_messages)
            # calculate_sentiment_and_save(messages)

            # logging.info("Running APOC to update sentiments...")
            result = session.write_transaction(update_sentiments_with_apoc)
            if result["errorMessages"]:
                logging.error(
                    f"Encountered errors during APOC update: {result['errorMessages']}"
                )
            logging.info(
                f"Updated sentiments in {result['batches']} batch(es), {result['total']} total updates."
            )

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        logging.info("Closing database connection...")
        driver.close()
