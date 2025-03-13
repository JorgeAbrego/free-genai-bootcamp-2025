import os
from pytube import YouTube
import groq
import tempfile
import json

# Configure Groq API
groq_client = groq.Client(api_key="your_groq_api_key")

def download_youtube_audio(url, output_path=None):
    """
    Downloads audio from a YouTube video.
    
    Args:
        url: YouTube video URL
        output_path: Path to save the file (optional)
    
    Returns:
        Path to the downloaded audio file
    """
    # If path is not specified, use a temporary directory
    if not output_path:
        temp_dir = tempfile.gettempdir()
        output_path = temp_dir
    
    try:
        yt = YouTube(url)
        # Get only the audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        # Download the audio
        downloaded_file = audio_stream.download(output_path=output_path)
        
        print(f"Audio downloaded: {downloaded_file}")
        return downloaded_file
    
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None

def transcribe_japanese_audio_groq(audio_path):
    """
    Transcribes a Japanese audio file using Groq's Whisper model.
    
    Args:
        audio_path: Path to the audio file
    
    Returns:
        Transcribed text in Japanese
    """
    try:
        with open(audio_path, "rb") as audio_file:
            # Prepare the file to send to the API
            audio_data = audio_file.read()
            
            # Send request to Groq using the Whisper model
            # Specify that the content is in Japanese
            response = groq_client.chat.completions.create(
                model="whisper-large-v3",  # Make sure to use the correct model name in Groq
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "This audio is in Japanese. Please transcribe it keeping the original Japanese text."
                            },
                            {
                                "type": "audio",
                                "data": audio_data
                            }
                        ]
                    }
                ]
            )
            
            # Get the transcription from the response
            transcription = response.choices[0].message.content
            return transcription
    
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None

def main():
    # YouTube video URL
    video_url = input("Enter the URL of the Japanese YouTube video: ")
    
    # Download the audio
    audio_file = download_youtube_audio(video_url)
    
    if audio_file:
        # Transcribe the Japanese audio
        print("Transcribing Japanese audio...")
        transcription = transcribe_japanese_audio_groq(audio_file)
        
        if transcription:
            print("\nVideo Transcription (Japanese):")
            print(transcription)
            
            # Save the transcription to a text file with appropriate encoding for Japanese
            file_name = os.path.basename(audio_file).split('.')[0] + "_transcription_jp.txt"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(transcription)
            
            print(f"\nTranscription saved to: {file_name}")
            
            # Ask if translation is also wanted
            translate = input("\nDo you also want a translation to English? (y/n): ").lower()
            if translate == 'y':
                try:
                    # Send translation request to Groq
                    translation_response = groq_client.chat.completions.create(
                        model="llama3-70b-8192",  # Or another LLM model available on Groq
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert translator from Japanese to English."
                            },
                            {
                                "role": "user",
                                "content": f"Translate the following text from Japanese to English:\n\n{transcription}"
                            }
                        ]
                    )
                    
                    translation = translation_response.choices[0].message.content
                    
                    print("\nEnglish Translation:")
                    print(translation)
                    
                    # Save the translation
                    trans_file_name = os.path.basename(audio_file).split('.')[0] + "_translation_en.txt"
                    with open(trans_file_name, "w", encoding="utf-8") as f:
                        f.write(translation)
                    
                    print(f"\nTranslation saved to: {trans_file_name}")
                    
                except Exception as e:
                    print(f"Error in translation: {e}")
        else:
            print("Could not obtain transcription.")
    else:
        print("Could not download video audio.")

if __name__ == "__main__":
    main()