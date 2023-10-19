if __name__ == "__main__":
    from neo4j import GraphDatabase

    uri = "bolt://localhost:7687"  # Replace with your Neo4j URI
    username = "neo4j"  # Replace with your username
    password = "password"  # Replace with your password

    driver = GraphDatabase.driver(uri, auth=(username, password))

    def get_messages(tx, username):
        query = (
            "MATCH (u:User)-[:SENT]->(m:Message) "
            "WHERE u.id = $username "
            "RETURN m.content AS messageContent"
        )
        result = tx.run(query, username=214580864082903050)
        return [record["messageContent"] for record in result]

    with driver.session() as session:
        messages = session.read_transaction(get_messages, "<USERNAME>")
        print(messages)
    from wordcloud import STOPWORDS

    # Combine messages into one text.
    text = " ".join(messages)

    # Optionally: add words that you don't want to include in the word cloud to STOPWORDS set.
    stopwords = set(STOPWORDS)
    # e.g., stopwords.update(["word1", "word2"])

    import matplotlib.pyplot as plt
    from wordcloud import WordCloud

    # Generate a word cloud
    wordcloud = WordCloud(
        width=800,  # Width of the canvas
        height=400,  # Height of the canvas
        background_color="white",  # Background color
        max_words=200,  # Maximum number of words
        stopwords=stopwords,
        scale=3,  # Scaling between computation and drawing. Higher means better resolution at larger sizes.
    ).generate(text)

    import matplotlib.pyplot as plt

    # Display the generated image with matplotlib
    plt.figure(
        figsize=(10, 5), dpi=300
    )  # The figsize and dpi can be adjusted to your needs
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()

    # Optionally: Save the word cloud as a high-res image
    # plt.savefig("wordcloud.png", format="png", dpi=300)
