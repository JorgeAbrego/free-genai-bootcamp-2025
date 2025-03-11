from invoke import task
from database import engine, Base, SessionLocal
from models import Group, StudyActivity, StudySession, WordGroup, WordReviewItem, WordReview, Word
import json

@task
def init_db(c):
    with engine.begin() as conn:
        print("Initilizing database...")
        Base.metadata.create_all(bind=conn)
        print("Database initialized.")
        
@task
def import_json_data(c):
    json_data = [
        {"group_name": "Core Verbs", "words_file": "seed/data_verbs.json"},
        {"group_name": "Core Adjectives", "words_file": "seed/data_adjectives.json"},
        {"activities_file": "seed/study_activities.json"}
    ]
    
    db = SessionLocal()
    try:
        # Process each dataset
        for data_set in json_data:
            # Load words if it contains group_name and words_file
            if "group_name" in data_set and "words_file" in data_set:
                group_name = data_set["group_name"]
                words_file = data_set["words_file"]
                
                # Create new group
                db_group = Group(name=group_name, words_count=0)
                db.add(db_group)
                db.flush()  # To get the generated ID
                
                # Load words from JSON
                try:
                    with open(words_file, 'r', encoding='utf-8') as file:
                        words_data = json.load(file)
                    
                    for word_data in words_data:
                        # Insert word
                        db_word = Word(
                            kanji=word_data.get('kanji', ''),
                            romaji=word_data.get('romaji', ''),
                            english=word_data.get('english', ''),
                            parts=word_data.get('parts', {})
                        )
                        db.add(db_word)
                        db.flush()  # To get the generated ID
                        
                        # Create word-group relationship
                        db_word_group = WordGroup(
                            word_id=db_word.id,
                            group_id=db_group.id
                        )
                        db.add(db_word_group)
                    
                    # Update word count in the group
                    db_group.words_count = len(words_data)
                    db.commit()
                    print(f"{len(words_data)} words were imported into the group '{group_name}'")
                except FileNotFoundError:
                    print(f"File not found: {words_file}")
                except Exception as e:
                    print(f"Error loading words for the group '{group_name}': {e}")
                    db.rollback()
            
            # Load study activities if it contains activities_file
            if "activities_file" in data_set:
                activities_file = data_set["activities_file"]
                
                try:
                    with open(activities_file, 'r', encoding='utf-8') as file:
                        activities_data = json.load(file)
                    
                    for activity in activities_data:
                        db_activity = StudyActivity(
                            name=activity.get('name', ''),
                            url=activity.get('url', ''),
                            preview_url=activity.get('preview_url', '')
                        )
                        db.add(db_activity)
                    
                    db.commit()
                    print(f"{len(activities_data)} study activities were imported")
                except FileNotFoundError:
                    print(f"File not found: {activities_file}")
                except Exception as e:
                    print(f"Error loading study activities: {e}")
                    db.rollback()
                    
        print("Data loading completed.")
    except Exception as e:
        db.rollback()
        print(f"General error loading data: {e}")
    finally:
        db.close()