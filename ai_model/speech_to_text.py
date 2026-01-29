"""
Speech-to-Text Transcription using OpenAI Whisper
Converts audio files to text for chat model processing
"""
import os
import requests
from openai import OpenAI
from django.conf import settings
from pathlib import Path


def transcribe_audio_with_whisper(audio_url: str, api_key: str = None, language: str = None) -> dict:

    """
    Transcribe audio file to text using OpenAI Whisper API
    
    Args:
        audio_url: URL or path to the audio file (can be local media URL or external URL)
        api_key: OpenAI API key (optional, will use default if not provided)
    
    Returns:
        dict: {"text": transcribed_text, "error": error_message}
    """
    try:
        # Use provided API key or fall back to settings
        if not api_key:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        if not api_key:
            return {"text": "", "error": "OpenAI API key not configured for transcription"}
        
        client = OpenAI(api_key=api_key)
        
        # Determine if it's a local media URL or starting with /media/
        is_local = False
        audio_path = ""
        
        if audio_url.startswith('/media/'):
            is_local = True
            audio_path = os.path.join(settings.MEDIA_ROOT, audio_url.replace('/media/', ''))
        elif settings.BASE_URL and audio_url.startswith(settings.BASE_URL) and '/media/' in audio_url:
            is_local = True
            path_part = audio_url.split('/media/')[-1]
            audio_path = os.path.join(settings.MEDIA_ROOT, path_part)
            
        if is_local:
            if not os.path.exists(audio_path):
                return {"text": "", "error": f"Audio file not found at {audio_path}"}
            
            # Open and transcribe local file
            with open(audio_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language
                )

            
            # Extract text from response
            text = transcript.text if hasattr(transcript, 'text') else str(transcript)
            
            return {"text": text.strip(), "error": None}
        
        # Handle external URLs - download first
        elif audio_url.startswith('http://') or audio_url.startswith('https://'):
            # Add browser headers just in case
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(audio_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save temporarily
            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Get file extension from URL or default to .mp3
            file_ext = Path(audio_url).suffix or '.mp3'
            temp_path = os.path.join(temp_dir, f"temp_audio_{os.getpid()}{file_ext}")
            
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Transcribe
            try:
                with open(temp_path, 'rb') as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language
                    )

                
                # Extract text from response
                text = transcript.text if hasattr(transcript, 'text') else str(transcript)
                result = {"text": text.strip(), "error": None}
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            return result
        
        else:
            return {"text": "", "error": "Invalid audio URL format"}
    
    except Exception as e:
        print(f"ERROR in transcribe_audio_with_whisper: {str(e)}")
        return {"text": "", "error": f"Transcription failed: {str(e)}"}
