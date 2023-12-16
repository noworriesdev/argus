\connect postgres;

CREATE SCHEMA IF NOT EXISTS operational;

CREATE TABLE operational.graph_streaming_checkpoints (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    channel BIGINT,
    last_message_seen BIGINT
);
