import streamlit as st
import json
import os
import re
from groq import Groq

# Page configuration
st.set_page_config(
    page_title="Japanese Vocabulary Generator",
    page_icon="🇯🇵",
    layout="wide"
)

# App title and description
st.title("Japanese Vocabulary Generator")
st.markdown("Enter a topic to generate a Japanese vocabulary list related to that topic.")

# Sidebar for API key
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter your Groq API key", type="password")
    model_name = st.selectbox(
        "Select LLM model",
        ["deepseek-r1-distill-llama-70b", "qwen-2.5-32b", "llama-3.3-70b-versatile"]
    )
    num_words = st.slider("Number of words to generate", 3, 15, 5)

# Main content
topic = st.text_input("Enter a topic (e.g., food, travel, technology):")

# Function to clean and extract JSON from response
def extract_json(text):
    # Try to find JSON array in the text using regex
    pattern = r'\[\s*{.*}\s*\]'
    matches = re.search(pattern, text, re.DOTALL)
    
    if matches:
        potential_json = matches.group(0)
        try:
            return json.loads(potential_json)
        except:
            pass
    
    # If regex failed, try to extract content between code blocks
    if "```json" in text:
        try:
            json_str = text.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        except:
            pass
    elif "```" in text:
        try:
            json_str = text.split("```")[1].split("```")[0].strip()
            return json.loads(json_str)
        except:
            pass
    
    # Last resort: try to fix common JSON errors
    try:
        # Replace single quotes with double quotes
        fixed_text = text.replace("'", '"')
        # Remove any non-JSON content before first '['
        if '[' in fixed_text:
            fixed_text = fixed_text[fixed_text.find('['):]
        # Remove any non-JSON content after last ']'
        if ']' in fixed_text:
            fixed_text = fixed_text[:fixed_text.rfind(']')+1]
        return json.loads(fixed_text)
    except:
        raise ValueError("Could not parse JSON from the response")

# Function to call Groq API
def generate_vocabulary(topic, num_words, api_key, model):
    if not api_key:
        return None, "Please enter a Groq API key in the sidebar."
    
    client = Groq(api_key=api_key)
    
    prompt = f"""
    Generate a Japanese vocabulary list about "{topic}" with {num_words} words.
    
    Return ONLY a valid JSON array with this exact format:
    [
      {{
        "kanji": "Japanese word (can be in kanji, hiragana, or mix)",
        "romaji": "romanized pronunciation",
        "english": "English translation",
        "parts": [
          {{
            "kanji": "first character or component",
            "romaji": ["romanized pronunciation of this component"]
          }},
          {{
            "kanji": "second character or component",
            "romaji": ["romanized pronunciation(s) of this component"]
          }}
        ]
      }}
    ]
    
    Important requirements:
    1. For each word, break it down into its individual characters or components
    2. For each component, provide its romanized pronunciation
    3. Ensure the JSON format is valid and exactly as shown above
    4. Do not include any explanations, markdown, or text outside the JSON array
    5. Only provide the raw JSON array
    
    Example for context (don't use these words unless relevant):
    [
      {{
        "kanji": "いい",
        "romaji": "ii",
        "english": "good",
        "parts": [
          {{
            "kanji": "い",
            "romaji": ["i"]
          }},
          {{
            "kanji": "い",
            "romaji": ["i"]
          }}
        ]
      }}
    ]
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Japanese vocabulary with detailed breakdowns of components. You ALWAYS return a valid JSON array and nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        # Extract the response text
        result = response.choices[0].message.content
        
        # Parse and validate the JSON
        vocabulary = extract_json(result)
        
        # Additional validation to ensure expected format
        for word in vocabulary:
            if not all(key in word for key in ["kanji", "romaji", "english", "parts"]):
                raise ValueError("JSON response doesn't match the expected format")
        
        return vocabulary, None
    except Exception as e:
        return None, f"Error: {str(e)}"

# Generate button
if st.button("Generate Vocabulary"):
    if not topic:
        st.error("Please enter a topic.")
    else:
        with st.spinner("Generating vocabulary..."):
            vocabulary, error = generate_vocabulary(topic, num_words, api_key, model_name)
            
            if error:
                st.error(error)
                st.info("Troubleshooting tips: Check your API key and internet connection. Try a different model or refresh the page.")
            else:
                # Display the vocabulary
                st.subheader(f"Japanese Vocabulary for: {topic}")
                
                # Create columns for displaying vocabulary
                cols = st.columns(min(3, len(vocabulary)))
                
                # Display each word in a card
                for i, word in enumerate(vocabulary):
                    col_index = i % len(cols)
                    with cols[col_index]:
                        st.markdown(f"""
                        <div style="border:1px solid #ddd; padding:10px; border-radius:5px; margin-bottom:10px;">
                            <h3>{word['kanji']}</h3>
                            <p><strong>Romaji:</strong> {word['romaji']}</p>
                            <p><strong>English:</strong> {word['english']}</p>
                            <details>
                                <summary>Word Components</summary>
                                <ul>
                                {''.join([f"<li>{part['kanji']} - {', '.join(part['romaji'])}</li>" for part in word['parts']])}
                                </ul>
                            </details>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Display raw JSON
                with st.expander("View Raw JSON"):
                    st.json(vocabulary)
                    
                # Download button for the JSON
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(vocabulary, indent=2, ensure_ascii=False),
                    file_name=f"{topic}_japanese_vocabulary.json",
                    mime="application/json"
                )

# Add debugging expander
with st.expander("Debug Information", expanded=False):
    st.markdown("""
    ### Troubleshooting
    
    If you encounter JSON parsing errors:
    
    1. Check that your API key is valid
    2. Try a different model (some models may produce better JSON formatting)
    3. Reduce the number of words requested
    4. Check the raw response from the API in the 'View Raw JSON' section
    
    Common issues:
    - The API sometimes returns explanatory text with the JSON
    - The response might include markdown formatting
    - Some models may not follow the exact JSON format requested
    """)

# Footer
st.markdown("---")
st.markdown("This app uses the Groq API to generate responses. You'll need to provide your own API key.")