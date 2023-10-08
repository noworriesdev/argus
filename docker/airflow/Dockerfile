# docker/airflow/Dockerfile

FROM apache/airflow:latest

# Set the working directory to /usr/src/app
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY requirements.txt .

USER airflow
RUN echo $(pwd)  # Will print "/usr/src/app"
RUN pip install --no-cache-dir -r requirements.txt
