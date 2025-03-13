from typing import Optional, Dict, List
import os
from groq import Groq
import time

# Groq configuration
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")  # Configure your API key environment variable
GROQ_MODEL = "llama-3.3-70b-versatile"  # Add your preferred model

class TranscriptStructurer:
    def __init__(self, model_id: str = GROQ_MODEL):
        """Initialize Groq client using the official library"""
        self.api_key = GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable must be set")
        
        self.model_id = model_id
        self.client = Groq(api_key=self.api_key)
        
        self.prompts = {
            1: """Extract questions from section 問題1 of this JLPT transcript where the answer can be determined solely from the conversation without needing visual aids.
            
            ONLY include questions that meet these criteria:
            - The answer can be determined purely from the spoken dialogue
            - No spatial/visual information is needed (like locations, layouts, or physical appearances)
            - No physical objects or visual choices need to be compared
            
            For example, INCLUDE questions about:
            - Times and dates
            - Numbers and quantities
            - Spoken choices or decisions
            - Clear verbal directions
            
            DO NOT include questions about:
            - Physical locations that need a map or diagram
            - Visual choices between objects
            - Spatial arrangements or layouts
            - Physical appearances of people or things

            Format each question exactly like this:

            <question>
            Introduction:
            [the situation setup in japanese]
            
            Conversation:
            [the dialogue in japanese]
            
            Question:
            [the question being asked in japanese]

            Options:
            1. [first option in japanese]
            2. [second option in japanese]
            3. [third option in japanese]
            4. [fourth option in japanese]
            </question>

            Rules:
            - Only extract questions from the 問題1 section
            - Only include questions where answers can be determined from dialogue alone
            - Ignore any practice examples (marked with 例)
            - Do not translate any Japanese text
            - Do not include any section descriptions or other text
            - Output questions one after another with no extra text between them
            """,
            
            2: """Extract questions from section 問題2 of this JLPT transcript where the answer can be determined solely from the conversation without needing visual aids.
            
            ONLY include questions that meet these criteria:
            - The answer can be determined purely from the spoken dialogue
            - No spatial/visual information is needed (like locations, layouts, or physical appearances)
            - No physical objects or visual choices need to be compared
            
            For example, INCLUDE questions about:
            - Times and dates
            - Numbers and quantities
            - Spoken choices or decisions
            - Clear verbal directions
            
            DO NOT include questions about:
            - Physical locations that need a map or diagram
            - Visual choices between objects
            - Spatial arrangements or layouts
            - Physical appearances of people or things

            Format each question exactly like this:

            <question>
            Introduction:
            [the situation setup in japanese]
            
            Conversation:
            [the dialogue in japanese]
            
            Question:
            [the question being asked in japanese]
            </question>

            Rules:
            - Only extract questions from the 問題2 section
            - Only include questions where answers can be determined from dialogue alone
            - Ignore any practice examples (marked with 例)
            - Do not translate any Japanese text
            - Do not include any section descriptions or other text
            - Output questions one after another with no extra text between them
            """,
            
            3: """Extract all questions from section 問題3 of this JLPT transcript.
            Format each question exactly like this:

            <question>
            Situation:
            [the situation in japanese where a phrase is needed]
            
            Question:
            何と言いますか
            </question>

            Rules:
            - Only extract questions from the 問題3 section
            - Ignore any practice examples (marked with 例)
            - Do not translate any Japanese text
            - Do not include any section descriptions or other text
            - Output questions one after another with no extra text between them
            """
        }

    def _invoke_groq(self, prompt: str, transcript: str) -> Optional[str]:
        """Make a single call to Groq API with the given prompt using the official library"""
        full_prompt = f"{prompt}\n\nHere's the transcript:\n{transcript}"
        
        try:
            # Adding some basic retries to handle potential API errors
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model_id,
                        messages=[
                            {"role": "user", "content": full_prompt}
                        ],
                        temperature=0
                    )
                    return completion.choices[0].message.content
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"Retry {attempt+1}/{max_retries} after error: {str(e)}")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # exponential backoff
                    else:
                        raise
        except Exception as e:
            print(f"Error invoking Groq API: {str(e)}")
            return None

    def structure_transcript(self, transcript: str) -> Dict[int, str]:
        """Structure the transcript into three sections using separate prompts"""
        results = {}
        # Process all sections (1, 2, 3)
        for section_num in range(1, 4):
            print(f"Processing section {section_num}...")
            result = self._invoke_groq(self.prompts[section_num], transcript)
            if result:
                results[section_num] = result
                print(f"Successfully processed section {section_num}")
            else:
                print(f"Failed to process section {section_num}")
        return results

    def save_questions(self, structured_sections: Dict[int, str], base_filename: str) -> bool:
        """Save each section to a separate file"""
        try:
            # Create questions directory if it doesn't exist
            os.makedirs(os.path.dirname(base_filename), exist_ok=True)
            
            # Save each section
            for section_num, content in structured_sections.items():
                filename = f"{os.path.splitext(base_filename)[0]}_section{section_num}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Saved section {section_num} to {filename}")
            return True
        except Exception as e:
            print(f"Error saving questions: {str(e)}")
            return False

    def load_transcript(self, filename: str) -> Optional[str]:
        """Load transcript from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading transcript: {str(e)}")
            return None

if __name__ == "__main__":
    # Make sure you have configured the environment variable GROQ_API_KEY
    structurer = TranscriptStructurer()
    transcript_path = "./data/transcripts/JNaUeTxSgqQ.txt"
    print(f"Loading transcript from {transcript_path}")
    transcript = structurer.load_transcript(transcript_path)
    
    if transcript:
        print(f"Transcript loaded successfully ({len(transcript)} characters)")
        structured_sections = structurer.structure_transcript(transcript)
        
        if structured_sections:
            output_path = "./data/questions/JNaUeTxSgqQ.txt"
            success = structurer.save_questions(structured_sections, output_path)
            if success:
                print(f"Questions successfully extracted and saved to {output_path}")
            else:
                print("Failed to save questions")
        else:
            print("No sections were processed successfully")
    else:
        print("Failed to load transcript")