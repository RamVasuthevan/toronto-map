# Use the specified Python base image
FROM python:3.11.5

# Install system dependencies for SpatiaLite and SQLite
RUN apt-get update && \
    apt-get install -y libsqlite3-mod-spatialite spatialite-bin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install pipenv
RUN pip install --upgrade pip && \
    pip install pipenv

# Echo the command to activate the virtual environment upon container start (if Pipfile exists)
RUN echo 'if [ -f "Pipfile" ]; then source $(pipenv --venv)/bin/activate; fi' >> ~/.bashrc
