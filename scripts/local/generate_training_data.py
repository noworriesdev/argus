from neo4j import GraphDatabase
import numpy as np
from sklearn.cluster import DBSCAN
import ipdb
import datetime
from datetime import datetime, timezone

import json
import tiktoken  # for token counting
import numpy as np
from collections import defaultdict


# Convert ISO8601 formatted string to UNIX timestamp (seconds since epoch)
def to_unix_timestamp(iso8601_string):
    dt = datetime.fromisoformat(iso8601_string)
    return dt.timestamp()


def cluster_messages_from_neo4j():
    from neo4j import GraphDatabase
    import json
    import os

    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_USERNAME")
    neo4j_host = os.getenv("NEO4J_HOST")
    neo4j_port = os.getenv("NEO4J_PORT")

    uri = f"bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=(neo4j_username, neo4j_password))

    final_clusters = []

    def get_channels(tx):
        result = tx.run("MATCH (c:Channel) RETURN c.id")
        return [record["c.id"] for record in result]

    def get_channel_messages_and_timestamps(tx, channel_id):
        query = (
            "MATCH (m:Message)-[:CONTAINED_IN]->(c:Channel), (u:User)-[:SENT]->(m) "
            "WHERE c.id = $channel_id "
            "RETURN m.id, m.content, m.timestamp, u.id AS user_id ORDER BY m.timestamp"
        )
        result = tx.run(query, channel_id=channel_id)
        return [
            {
                "id": record["m.id"],
                "content": record["m.content"],
                "timestamp": record["m.timestamp"],
                "user_id": record["user_id"],
            }
            for record in result
        ]

    def to_unix_timestamp(iso8601_string):
        dt = datetime.fromisoformat(iso8601_string)
        return dt.timestamp()

    with driver.session() as session:
        channel_ids = session.read_transaction(get_channels)
    for channel_id in channel_ids:
        with driver.session() as session:
            messages = session.read_transaction(
                get_channel_messages_and_timestamps, channel_id
            )

        # Ensure messages are there to analyze
        if not messages:
            print(f".")
        else:
            # Convert timestamps to Unix timestamps and then to a NumPy array
            timestamps_unix = [to_unix_timestamp(msg["timestamp"]) for msg in messages]
            timestamps_array = (
                np.array(timestamps_unix).reshape(-1, 1).astype(np.float64)
            )

            # Define and fit the DBSCAN model
            epsilon = 60 * 60  # we're clustering messages in 60-minute intervals
            min_samples = 5  # Minimum number of messages in a cluster

            model = DBSCAN(eps=epsilon, min_samples=min_samples, metric="euclidean")
            labels = model.fit_predict(timestamps_array)

            # Initialize a dictionary to hold messages by cluster label
            clusters = {i: [] for i in set(labels)}

            # Assign messages to clusters
            for message, label in zip(messages, labels):
                clusters[label].append(message)

            # Convert clusters to list format and handle noise if you want
            synthesized_labels = [
                clusters[label] for label in sorted(clusters.keys()) if label != -1
            ]
            for label in synthesized_labels:
                final_clusters.append(label)
    return final_clusters


import copy


def get_word_count(cluster):
    return sum(len(message["content"].split()) for message in cluster)


def break_cluster(cluster, max_words=3250):
    new_clusters = []
    current_cluster = []
    current_word_count = 0

    for message in cluster:
        message_word_count = len(message["content"].split())

        if current_word_count + message_word_count <= max_words:
            current_cluster.append(message)
            current_word_count += message_word_count
        else:
            new_clusters.append(copy.deepcopy(current_cluster))
            current_cluster = [message]
            current_word_count = message_word_count

    # Append the last cluster if it's not empty
    if current_cluster:
        new_clusters.append(current_cluster)

    return new_clusters


def process_clusters(original_clusters):
    new_clusters = []

    for cluster in original_clusters:
        if get_word_count(cluster) > 2500:
            new_clusters.extend(break_cluster(cluster))
        else:
            new_clusters.append(cluster)

    return new_clusters


def get_user_word_counts(cluster):
    """Get a dictionary of word counts per user for a cluster."""
    user_word_counts = {}

    for message in cluster:
        user_id = message["user_id"]
        word_count = len(message["content"].split())
        user_word_counts[user_id] = user_word_counts.get(user_id, 0) + word_count

    return user_word_counts


def user_dominates_cluster(user_word_counts, user_id, total_word_count, threshold):
    try:
        # Ensure user_id is in user_word_counts and total_word_count is not zero
        if user_id in user_word_counts and total_word_count != 0:
            return user_word_counts[user_id] / total_word_count >= threshold
        else:
            return False
    except TypeError as e:
        print(f"TypeError: {e}")
        return False


def get_dominating_user_clusters(original_clusters, user_id, threshold=0.25):
    """Get clusters where the specified user contributed a percentage of words at least equal to the threshold."""
    dominating_user_clusters = []

    for cluster in original_clusters:
        user_word_counts = get_user_word_counts(
            cluster
        )  # get word counts for each user in cluster
        total_word_count = get_word_count(
            cluster
        )  # get total word count for the cluster

        if user_dominates_cluster(
            user_word_counts, user_id, total_word_count, threshold
        ):
            dominating_user_clusters.append(cluster)

    return dominating_user_clusters


def convert_cluster_to_tuning_structure(cluster, assistant_id):
    results_dict = {
        "messages": [
            {
                "role": "system",
                "content": "You are Victoria Bot, an autonomous being. You are trained to emulate the behavior of Lucy, a real human. You should express yourself truthfully in all interactions.",
            }
        ]
    }
    for message in cluster:
        if message["user_id"] == assistant_id:
            results_dict["messages"].append(
                {"role": "assistant", "content": message["content"]}
            )
        else:
            results_dict["messages"].append(
                {"role": "user", "content": message["content"]}
            )
    return results_dict


if __name__ == "__main__":
    lucy_id = None
    clusters = cluster_messages_from_neo4j()
    shortened_clusters = process_clusters(clusters)
    lucy_clusters = get_dominating_user_clusters(shortened_clusters, lucy_id)
    json_to_dump = [
        convert_cluster_to_tuning_structure(cluster, lucy_id)
        for cluster in lucy_clusters
    ]
    with open("local_data/training_data/output.jsonl", "w", encoding="utf-8") as f:
        # Go through each dictionary in the list.
        for entry in json_to_dump:
            # Check if there is a 'user' entry, and add a placeholder if not
            if not any(message["role"] == "user" for message in entry["messages"]):
                entry["messages"].append(
                    {"role": "user", "content": "what do you think, Lucy?"}
                )

            # Convert the dictionary to a JSON string and write it to the file.
            # Use ensure_ascii=False to preserve non-ASCII characters.
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    # ipdb.set_trace()
