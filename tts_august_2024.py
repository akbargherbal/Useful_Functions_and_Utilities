import os
import logging
from google.cloud import texttospeech
from time import sleep
from datetime import datetime
import pandas as pd

# Set up directories and logging
TIME_STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
MAIN_DIR = f"FREELANCE_AUDIOBOOK_{TIME_STAMP}"

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

log_file = f"{TIME_STAMP}_tts_log.txt"
file_handler = logging.FileHandler(log_file, mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger('').addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger('').addHandler(console_handler)

# Initialize Google Cloud Text-to-Speech client
client = texttospeech.TextToSpeechClient()

def synthesize_text_to_speech(text_content, voice_name, output_filename, folder):
    """
    Synthesizes speech from a given text string and saves it to an audio file.

    Args:
        text_content (str): The text content to synthesize.
        output_filename (str): The name of the output audio file (default: "output.mp3").
        folder (str): The folder to save the audio file in.
        voice_name (str): The name of the voice to use for synthesis.

    Raises:
        Exception: If the synthesis request fails.
    """
    try:
        if not output_filename.endswith(".mp3"):
            output_filename += ".mp3"

        full_folder_path = os.path.join(MAIN_DIR, folder)
        if not os.path.exists(full_folder_path):
            os.makedirs(full_folder_path)

        file_path = os.path.join(full_folder_path, output_filename)
        input_text = texttospeech.SynthesisInput(text=text_content)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", name=voice_name
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16, speaking_rate=1
        )
        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )
        with open(file_path, "wb") as out:
            out.write(response.audio_content)
            logging.info(f'Audio content written to file "{file_path}"')
        return True
    except Exception as e:
        logging.error(f"Synthesis request failed: {e}")
        return False

if __name__ == "__main__":
    # Explicitly set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    path_to_api_json_key = input('Enter path to GCP JSON credentials file:\n')
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path_to_api_json_key

    # Create the main directory
    if not os.path.exists(MAIN_DIR):
        os.makedirs(MAIN_DIR)

    # Load text content
    df = pd.read_pickle('./TEXT_CONTENT_INPUT_TO_TTS.pkl')
    list_text_content = list(zip(df['FOLDER'], df['TEXT']))

    wait_time = 15
    voice = "en-US-Journey-O"

    succeeded = []
    failed = []

    for idx, (folder, text) in enumerate(list_text_content, start=1):
        start_time = datetime.now()
        try:
            success = synthesize_text_to_speech(folder=folder, text_content=text, voice_name=voice, output_filename=f'{str(idx).zfill(2)}.mp3')
            if success:
                succeeded.append(idx)
            else:
                failed.append(idx)
        except Exception as e:
            logging.error(f"Error processing text {idx}: {e}")
            failed.append(idx)
            continue

        end_time = datetime.now()
        time_diff = (end_time - start_time).total_seconds()
        if time_diff < wait_time:
            logging.info(f'Sleeping for {round(wait_time - time_diff)} seconds')
            sleep(wait_time - time_diff)

    # Log the final results
    logging.info(f"Succeeded: {succeeded}")
    logging.info(f"Failed: {failed}")

    print(f"Script execution completed. Check the log file: {log_file}")
