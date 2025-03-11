## Install

First, create a virtual environment using a manager (e.g., conda, venv), then install the dependencies listed in the `requirements.txt` file:

```sh
pip install -r requirements.txt
```

## Setting Up the Database

To create the words.db (Sqlite3 database), run:

```sh
invoke init-db
```

## Populating tables

To populate database tables with sample data, run:

```sh
invoke import-json-data
```

## Running the Backend API

Start the FastAPI app on port 8000 with:

```sh
uvicorn main:app --reload
```
