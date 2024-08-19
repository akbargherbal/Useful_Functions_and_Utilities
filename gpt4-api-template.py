import os
import sys
import time
import logging
from datetime import datetime

import openai
from openai import OpenAI
import pandas as pd
import regex as re

# User-defined constants
SYSTEM_PROMPT = 'You are a helpful assistant and a web development expert.'
GPT4_MODEL = "gpt-4o-2024-08-06"
MAX_TOKENS = 4096
PROMPT_INDEX_COLUMN = 'prompt_id'  # Name of the column containing prompt indices
PROMPT_COLUMN = 'prompt'  # Name of the column containing the actual prompts
MAX_DELAY = 12  # Maximum delay between API calls in seconds

# Time-stamped log file and output directories
TIME_STAMP = datetime.now().strftime("%Y%m%d%H%M%S")
LogFileName = f"LOG_{TIME_STAMP}.log"
PKL_FILE_NAME = f"RESULTS_{TIME_STAMP}.pkl"
DIR_RESULT = f"results_{TIME_STAMP}"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(LogFileName), logging.StreamHandler()])

# Create directory to save results if it doesn't exist
os.makedirs(DIR_RESULT, exist_ok=True)

def setup_openai_api():
    """Set up the OpenAI API key."""
    logging.info("OpenAI API key not found in environment variables. Please enter it now.")
    print("OpenAI API key not found in environment variables. Please enter it now.")
    api_key = input("Paste your OpenAI API key: ").strip()
    
    client = OpenAI(api_key=api_key)
    
    try:
        client.models.list()
        logging.info("OpenAI API authentication successful.")
    except openai.AuthenticationError:
        logging.error("Authentication failed. Please check your API key.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while setting up the OpenAI API: {str(e)}")
        sys.exit(1)
    
    return client

def generate_response(client, prompt_text, prompt_id):
    """Generate a response using OpenAI API based on user input."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt_text}
    ]

    try:
        response = client.chat.completions.create(
            model=GPT4_MODEL,
            messages=messages,
            temperature=1,
            max_tokens=MAX_TOKENS,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        prefix = str(prompt_id).zfill(4)
        result_content = response.choices[0].message.content
        result_file_name = re.sub(r'\W+', '_', "result").lower()
        result_file_name = f"{prefix}_{result_file_name}.txt"
        with open(f"./{DIR_RESULT}/{result_file_name}", "w", encoding="utf-8") as f:
            f.write(result_content)

        return result_content, response
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")
        return None, None

def process_prompts(client, path_to_prompts):
    """Process prompts and generate responses."""
    try:
        df = pd.read_pickle(path_to_prompts)
        print(f"Columns in the dataframe: {list(df.columns)}")
    except FileNotFoundError:
        logging.error(f"Input file {path_to_prompts} not found.")
        return
    except Exception as e:
        logging.error(f"Error reading input file: {str(e)}")
        return

    prompts_list = list(zip(df[PROMPT_INDEX_COLUMN], df[PROMPT_COLUMN]))
    
    results_list = []
    
    total_prompts_count = len(prompts_list)
    for index, (prompt_id, prompt_text) in enumerate(prompts_list, 1):
        # Check if this prompt has already been processed
        if any(item['PROMPT_ID'] == prompt_id for item in results_list):
            logging.info(f"Skipping prompt {index} (ID: {prompt_id}) as it's already processed.")
            continue

        logging.info(f"Processing prompt {index} of {total_prompts_count}")
        print(f"Processing prompt {index} of {total_prompts_count}")
        start = datetime.now()
        result_content, response = generate_response(client, prompt_text, prompt_id)
        if result_content:
            results_list.append({'PROMPT_ID': prompt_id, 'RESULT': result_content, 'RESPONSE': response})
            df_result = pd.DataFrame(results_list)
            try:
                df_result.to_pickle(f'./{PKL_FILE_NAME}', protocol=4)
                logging.info(f"Intermediate results saved for prompt {index}")
            except Exception as e:
                logging.error(f"Error saving intermediate results: {str(e)}")
                print(f"Error saving intermediate results: {str(e)}")
        
        # Rate limiting
        end = datetime.now()
        sleep_time = max(MAX_DELAY - (end - start).total_seconds(), 0)
        if sleep_time > 0:
            logging.info(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)

    logging.info(f"Processing complete. {len(results_list)} out of {total_prompts_count} prompts processed successfully.")
    logging.info(f"Results saved to {DIR_RESULT} and {PKL_FILE_NAME}")
    print(f"Processing complete. {len(results_list)} out of {total_prompts_count} prompts processed successfully.")
    print(f"Results saved to {DIR_RESULT} and {PKL_FILE_NAME}")

def main():
    path_to_prompts = input("Enter the path to the PKL file containing prompts: ").strip()
    client = setup_openai_api()
    process_prompts(client, path_to_prompts)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)
