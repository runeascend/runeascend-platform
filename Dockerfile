# Use the official Python image as the base image
FROM python:3.11

# Upgrade PIP
RUN pip install --upgrade pip

# Set the working directory in the container
WORKDIR /app

# Copy the project files to the container
COPY runeascend /app/runeascend
COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock
COPY README.md /app/README.md

# Install poetry
RUN pip install poetry==1.4.2

# Install project dependencies
RUN poetry install 


