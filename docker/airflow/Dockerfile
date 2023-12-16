# docker/airflow/Dockerfile

FROM apache/airflow:latest

# Set the working directory to /usr/src/app
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY requirements.txt .
RUN pip install -r requirements.txt