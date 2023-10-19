if __name__ == "__main__":
    from neo4j import GraphDatabase

    uri = "bolt://localhost:7687"  # Replace with your Neo4j URI
    username = "neo4j"  # Replace with your username
    password = "password"  # Replace with your password

    driver = GraphDatabase.driver(uri, auth=(username, password))

    driver = GraphDatabase.driver(uri, auth=(username, password))

    def get_message_counts(tx):
        query = (
            "MATCH (u:User) "
            "OPTIONAL MATCH (u)-[:SENT]->(m:Message) "
            "RETURN u.name AS name, COALESCE(COUNT(m), 0) AS messageCount "
            "ORDER BY messageCount ASC"
        )
        result = tx.run(query)
        return [(record["name"], record["messageCount"]) for record in result]

    with driver.session() as session:
        data = session.read_transaction(get_message_counts)

    import matplotlib.pyplot as plt

    # Ensure you've got the `data` from Neo4j
    names, message_counts = zip(*data)  # Unzipping the data into two lists

    # Create a vertical bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(names, message_counts, color="skyblue")  # vertical bar chart
    plt.ylabel("Number of Messages Sent")
    plt.xlabel("User")
    plt.title("Number of Messages Sent by User")
    plt.xticks(rotation=90)  # Rotate labels for better readability
    plt.tight_layout()  # Adjust layout to prevent clipping of labels

    # Display the plot
    plt.show()
