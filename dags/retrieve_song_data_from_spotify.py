from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from neo4j import GraphDatabase
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# DAG Configuration
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 1,
}
dag = DAG(
    'spotify_song_info',
    default_args=default_args,
    description='Update Song nodes with Spotify data using Spotipy',
    schedule_interval=None,
)

# Spotify API Credentials (Replace with your credentials)
spotify_client_id = '5332bac437124b708b0401bcf8b3d105'
spotify_client_secret = 'e330b8b5e37d459abb162ba089041215'

# Neo4j Connection (Update with your connection details)
neo4j_conn_uri = "bolt://argus-neo4j:7687"
neo4j_username = "neo4j"
neo4j_password = "mycoolpassword"

# Initialize Neo4j Connection
def get_neo4j_driver():
    return GraphDatabase.driver(neo4j_conn_uri, auth=(neo4j_username, neo4j_password))

# Initialize Spotify Client with Spotipy
def get_spotify_client():
    client_credentials_manager = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    return sp

def update_song_nodes(**kwargs):
    driver = get_neo4j_driver()
    sp = get_spotify_client()

    with driver.session() as session:
        songs = session.run("MATCH (song:Song) <-[:POSTED_SONG]- (u:User) RETURN song.spotifyId as spotify_id, u.userId as user_id, u.name as name")

        for record in songs:
            spotify_id = record["spotify_id"]
            user_id = record["user_id"]
            name = record["name"]
            print(user_id)
            print(name)
            try:
                track = sp.track(spotify_id)
                album_id = track["album"]["id"]
                album_name = track["album"]["name"]
                artists = [(artist["id"], artist["name"]) for artist in track["artists"]]

                # Update Song node
                session.run(
                    "MATCH (song:Song {spotifyId: $spotify_id}) "
                    "SET song.name = $name ",
                    spotify_id=spotify_id,
                    name=track["name"],
                )

                # Create or update Album node
                session.run(
                    "MERGE (album:Album {spotifyId: $album_id}) "
                    "MERGE (user:User {userId: $user_id}) "
                    "SET album.name = $album_name "
                    "MERGE (user) -[:REFERENCED_ALBUM]-> (album)",
                    album_id=album_id,
                    album_name=album_name,
                    user_id = user_id
                )

                # Create relationship between Song and Album
                session.run(
                    "MATCH (song:Song {spotifyId: $spotify_id}) "
                    "MATCH (album:Album {spotifyId: $album_id}) "
                    "MERGE (song)-[:BELONGS_TO]->(album)",
                    spotify_id=spotify_id,
                    album_id=album_id
                )

                # Create or update Artist nodes and relationships
                for artist_id, artist_name in artists:
                    session.run(
                        "MERGE (artist:Artist {spotifyId: $artist_id}) "
                        "MERGE (user:User {userId: $user_id}) "
                        "MERGE (album:Album {spotifyId: $album_id}) "
                        "MERGE (artist)-[:AUTHORED]->(album) "
                        "MERGE (user)-[:POSTED_ARTIST]->(artist)"
                        "SET artist.name = $artist_name ",
                        artist_id=artist_id,
                        artist_name=artist_name,
                        album_id=album_id,
                        user_id=user_id
                    )

            except spotipy.exceptions.SpotifyException as e:
                print(f"Error fetching data for Spotify ID {spotify_id}: {e}")


# Python Operator to Update Song Nodes
update_song_nodes_task = PythonOperator(
    task_id='update_song_nodes',
    python_callable=update_song_nodes,
    dag=dag,
)

update_song_nodes_task
