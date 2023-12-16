import hashlib
import uuid

def hash_to_uuid(user, message, reaction):
    combined = f"{user}|{message}|{reaction}"
    
    combined_bytes = combined.encode('utf-8')

    hash_bytes = hashlib.sha256(combined_bytes).digest()

    return uuid.UUID(bytes=hash_bytes[:16])

uuid_result = hash_to_uuid("string1", "string2", "🙂")
print(uuid_result)


def generate_csvs_from_json():
    from neo4j import GraphDatabase
    import json
    import os
    import csv
    import hashlib
    import uuid
    
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_USERNAME")
    neo4j_host = os.getenv("NEO4J_HOST")
    neo4j_port = os.getenv("NEO4J_PORT")

    uri = f"bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=(neo4j_username, neo4j_password))

    with open("./local_data/discord_json_dump/discord_messages.json", "r") as f:
        channel_messages = json.load(f)

    # Prepare lists for entities and relationships
    users = []
    messages = []
    channels = []
    reactions = []
    user_message_rel = []
    message_channel_rel = []
    message_mention_rel = []
    message_reaction_rel = []
    user_reaction_rel = []
    for channel_id, channel_data in channel_messages.items():
        channels.append([channel_data["info"]["id"], channel_data["info"]["name"]])

        for message in channel_data["messages"]:
            # Add user if not already in the list
            if not any(u[0] == message["author_id"] for u in users):
                users.append([message["author_id"], message["author_name"]])

            # Add message
            messages.append([message["id"], message["content"], message["timestamp"]])
            for mention in message.mentions:
                message_mention_rel.append(
                    [message["id"], mention, "MENTIONED"]
                )
            # Add relationships
            user_message_rel.append([message["author_id"], message["id"], "SENT"])
            message_channel_rel.append(
                [message["id"], channel_data["info"]["id"], "CONTAINED_IN"]
            )
            for emoji in message["reactions"].keys():
                """
                We are working with a dictionary like:
                    {
                        "fire_emoji": [
                            1, 2, 3
                        ],
                        "heart_emoji": [
                            1
                        ]
                    }
                """ 
                for user in message["reactions"][emoji]:
                    uuid = hash_to_uuid(message["author_id"], user, emoji)
                    reactions.append(
                        [
                            uuid,
                            emoji
                        ]
                    )
                    message_reaction_rel.append(
                        [message["id"], uuid, "HAS_REACTION"]
                    )
                    user_reaction_rel.append(
                        [user, uuid, "REACTED"]
                    )
                    

    # Write data to CSVs
    with open("local_data/csvs/users.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["userId:ID", "name"])
        writer.writerows(users)

    with open("local_data/csvs/reactions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["reactionId:ID", "emoji"])
        writer.writerows(reactions)

    with open("local_data/csvs/messages.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["messageId:ID", "content", "timestamp"])
        writer.writerows(messages)

    with open("local_data/csvs/channels.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["channelId:ID", "name"])
        writer.writerows(channels)

    with open(
        "local_data/csvs/user_message_rel.csv", "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        writer.writerow([":START_ID", ":END_ID", ":TYPE"])
        writer.writerows(user_message_rel)

    with open(
        "local_data/csvs/message_channel_rel.csv", "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        writer.writerow([":START_ID", ":END_ID", ":TYPE"])
        writer.writerows(message_channel_rel)

    with open(
        "local_data/csvs/message_mention_rel.csv", "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        writer.writerow([":START_ID", ":END_ID", ":TYPE"])
        writer.writerows(message_mention_rel)

    with open(
        "local_data/csvs/user_reaction_rel.csv", "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        writer.writerow([":START_ID", ":END_ID", ":TYPE"])
        writer.writerows(user_reaction_rel)

    with open(
        "local_data/csvs/message_reaction_rel.csv", "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f)
        writer.writerow([":START_ID", ":END_ID", ":TYPE"])
        writer.writerows(message_reaction_rel)        
if __name__ == "__main__":
    generate_csvs_from_json()
