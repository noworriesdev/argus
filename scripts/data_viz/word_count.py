from collections import Counter
import re
from neo4j import GraphDatabase

if __name__ == "__main__":
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "password"

    driver = GraphDatabase.driver(uri, auth=(username, password))

    def get_messages(tx, username):
        query = (
            "MATCH (u:User)-[:SENT]->(m:Message) "
            "WHERE u.id = $username "
            "RETURN m.content AS messageContent"
        )
        result = tx.run(query, username=username)
        return [record["messageContent"] for record in result]

    with driver.session() as session:
        messages = session.read_transaction(get_messages, 881729836371046492)
        print(messages)

    # Combine messages into one text.
    text = " ".join(messages)

    # Tokenize text into words, considering only alphanumeric words (omitting punctuation and special characters).
    words = re.findall(r"\b\w+\b", text.lower())

    # Optionally: exclude common stopwords. For a precise control, you might want to define your own set.
    stopwords = {
        "a",
        "an",
        "the",
        "in",
        "of",
        "to",
        "and",
        "on",
        "or",
        "is",
        "it",
        "that",
        "this",
        "you",
    }  # etc.
    words = [word for word in words if word not in stopwords]

    # Count occurrences of each word
    word_count = Counter(words)

    # Get the 100 most common words and their counts
    top_100_words = word_count.most_common(100)

    print("Top 100 words and their counts:")
    for word, count in top_100_words:
        print(f"{word}: {count}")
