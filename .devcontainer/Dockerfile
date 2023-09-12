FROM python:3.11.5

RUN rm -rf .venv

RUN pip install --upgrade pip && \
    pip install pipenv && \
    echo 'if [ -f "Pipfile" ]; then source $(pipenv --venv)/bin/activate; fi' >> ~/.bashrc