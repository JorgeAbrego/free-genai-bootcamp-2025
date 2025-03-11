# Backend Server Technical Sepcs

## Business Goal:

A language learning school wants to build a prototype of learning portal which will act as three things:
- Inventory of possible vocabulary that can be learned
- Act as a  Learning record store (LRS), providing correct and wrong score on practice vocabulary
- A unified launchpad to launch different learning apps

## Technical Requirements

- The backend will be built using Python
- The API will be built using FastAPI
- The database will be SQLite3
- The API will always return JSON
- There will no authentication or authorization
- Everything be treated as a single user

## Directory Structure

```text
backend_fastapi/
├── app/
│   └── routes/       # Routes organized by feature (dashboard, words, groups, etc.)
│   ├── seed/         # For initial data population
│   ├── database.py   # Database connection
│   ├── main.py       # FastAPI app entry point
│   ├── models.py     # Data structures
│   ├── schemas.py    # Pydantic models
│   └── tasks.py      # Task runner
└── requirements.txt  # File with all dependencies
```

## Database Schema

Our database will be a single sqlite database called `words.db` that will be in the root of the project folder of `backend-fastapi`

We have the following tables:
- words - stored vocabulary words
  - `id` (Primary Key): Unique identifier for each word
  - `kanji` (String, Required): The word written in Japanese kanji
  - `romaji` (String, Required): Romanized version of the word
  - `english` (String, Required): English translation of the word
  - `parts` (JSON, Required): Word components stored in JSON format
- words_groups - join table for words and groups many-to-many
  - `word_id` (Foreign Key): References words.id
  - `group_id` (Foreign Key): References groups.id
- groups - thematic groups of words
  - `id` (Primary Key): Unique identifier for each group
  - `name` (String, Required): Name of the group
  - `words_count` (Integer, Default: 0): Counter cache for the number of words in the group
- study_sessions - records of study sessions grouping word_review_items
  - `id` (Primary Key): Unique identifier for each session
  - `group_id` (Foreign Key): References groups.id
  - `study_activity_id` (Foreign Key): References study_activities.id
  - `created_at` (Timestamp, Default: Current Time): When the session was created
- study_activities - a specific study activity, linking a study session to group
  - `id` (Primary Key): Unique identifier for each activity
  - `name` (String, Required): Name of the activity (e.g., "Flashcards", "Quiz")
  - `url` (String, Required): The full URL of the study activity
- word_review_items - a record of word practice, determining if the word was correct or not
  - `id` (Primary Key): Unique identifier for each review
  - `word_id` (Foreign Key): References words.id
  - `study_session_id` (Foreign Key): References study_sessions.id
  - `correct` (Boolean, Required): Whether the answer was correct
  - `created_at` (Timestamp, Default: Current Time): When the review occurred


## API Endpoints

### Dashboard

#### GET /api/dashboard/recent_session
Returns information about the most recent study session.

<b>JSON Response</b>
```json
{
  "id": 0,
  "group_id": 0,
  "activity_name": "string",
  "created_at": "2025-03-10T01:27:14.181Z",
  "correct_count": 0,
  "wrong_count": 0
}
```

#### GET /api/dashboard/stats

Returns quick overview statistics.

<b>JSON Response</b>
```json
{
  "total_vocabulary": 0,
  "total_words_studied": 0,
  "mastered_words": 0,
  "success_rate": 0,
  "total_sessions": 0,
  "active_groups": 0,
  "current_streak": 0
}
```

### Study Activities

#### GET /api/study_activities

<b>JSON Response</b>
```json
[
  {
  "id": 1,
  "name": "Typing Tutor",
  "url": "http://localhost:8080",
  "preview_url": "/assets/study_activities/typing-tutor.png"
  }
]
```

#### GET /api/study_activities/:id

<b>JSON Response</b>
```json
{
  "id": 1,
  "name": "Vocabulary Quiz",
  "url": "https://example.com/thumbnail.jpg",
  "preview_url": "/assets/study_activities/vocabulary-quiz.png"
}
```

#### GET /api/study_activities/:id/study_sessions

- pagination with 100 items per page

```json
{
  "items": [
    {
      "id": 123,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Greetings",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "items_per_page": 20
  }
}
```

### Words

#### GET /api/words

- pagination with 100 items per page

<b>JSON Response</b>
```json
{
  "items": [
    {
      "japanese": "こんにちは",
      "romaji": "konnichiwa",
      "english": "hello",
      "correct_count": 5,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 500,
    "items_per_page": 100
  }
}
```

#### GET /api/words/:id

<b>JSON Response</b>
```json
{
  "japanese": "こんにちは",
  "romaji": "konnichiwa",
  "english": "hello",
  "stats": {
    "correct_count": 5,
    "wrong_count": 2
  },
  "groups": [
    {
      "id": 1,
      "name": "Basic Greetings"
    }
  ]
}
```

### Groups

#### GET /api/groups

- pagination with 100 items per page
<b>JSON Response</b>
```json
{
  "items": [
    {
      "id": 1,
      "name": "Basic Greetings",
      "word_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 10,
    "items_per_page": 100
  }
}
```

#### GET /api/groups/:id

<b>JSON Response</b>
```json
{
  "id": 1,
  "name": "Basic Greetings",
  "stats": {
    "total_word_count": 20
  }
}
```

#### GET /api/groups/:id/words

<b>JSON Response</b>
```json
{
  "items": [
    {
      "japanese": "こんにちは",
      "romaji": "konnichiwa",
      "english": "hello",
      "correct_count": 5,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 20,
    "items_per_page": 100
  }
}
```

#### GET /api/groups/:id/study_sessions

<b>JSON Response</b>
```json
{
  "items": [
    {
      "id": 123,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Greetings",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 5,
    "items_per_page": 100
  }
}
```

### Study Sessions

#### GET /api/study_sessions

- pagination with 100 items per page

<b>JSON Response</b>
```json
{
  "items": [
    {
      "id": 123,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Greetings",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "items_per_page": 100
  }
}
```

### GET /api/study_sessions/:id
<b>JSON Response</b>
```json
{
  "id": 123,
  "activity_name": "Vocabulary Quiz",
  "group_name": "Basic Greetings",
  "start_time": "2025-02-08T17:20:23-05:00",
  "end_time": "2025-02-08T17:30:23-05:00",
  "review_items_count": 20
}
```

### GET /api/study_sessions/:id/words
- pagination with 100 items per page
<b>JSON Response</b>
```json
{
  "items": [
    {
      "japanese": "こんにちは",
      "romaji": "konnichiwa",
      "english": "hello",
      "correct_count": 5,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 20,
    "items_per_page": 100
  }
}
```

### POST /api/reset_history
<b>JSON Response</b>
```json
{
  "success": true,
  "message": "Study history has been reset"
}
```

### POST /api/full_reset
<b>JSON Response</b>
```json
{
  "success": true,
  "message": "System has been fully reset"
}
```

### POST /api/study_sessions/:id/words/:word_id/review
#### Request Params
- id (study_session_id) integer
- word_id integer
- correct boolean

#### Request Payload
```json
{
  "correct": true
}
```

<b>JSON Response</b>
```json
{
  "success": true,
  "word_id": 1,
  "study_session_id": 123,
  "correct": true,
  "created_at": "2025-02-08T17:33:07-05:00"
}
```

## Task Runner Tasks

Lets list out possible tasks we need for our lang portal.

### Initialize Database

This task will initialize the sqlite database called `words.db

### Migrate Database

This task will run a series of migrations sql files on the database

Migrations live in the `tasks.py` file.

### Seed Data

This task will import json files and transform them into target data for our database.

All seed files live in the `seeds` folder.

In our task we should have DSL to specific each seed file and its expected group word name.

```json
[
  {
    "kanji": "払う",
    "romaji": "harau",
    "english": "to pay",
  },
  ...
]
```