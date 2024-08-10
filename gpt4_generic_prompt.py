import os
import sys
import time
import logging
from datetime import datetime

import openai
from openai import OpenAI
import pandas as pd
import regex as re

# Time-stamped log file
TIME_STAMP = datetime.now().strftime("%Y%m%d%H%M%S")
LogFileName = f"log_{TIME_STAMP}.log"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(LogFileName), logging.StreamHandler()])

# Create directory to save results if it doesn't exist
DIR_RESULT = f"results_{TIME_STAMP}"
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

def generate_generic_response(client, task_description):
    """Generate a generic response using OpenAI API based on user input."""
    messages = [
        {"role": "system", "content": "You're a helpful assistant."},
        {"role": "user", "content": task_description}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=1,
            max_tokens=4095,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        task_result = response.choices[0].message.content
        result_file_name = re.sub(r'\W+', '_', "result").lower()  # Generic file name
        result_file_name = f"{result_file_name}.txt"
        with open(f"./{DIR_RESULT}/{result_file_name}", "w", encoding="utf-8") as f:
            f.write(task_result)

        return task_result
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")
        return None

def process_tasks(client):
    """Process tasks and generate responses."""
    try:
        # Here we assume a more generic CSV file input for tasks
        df = pd.read_csv('./tasks.csv')
        print(df.head(2))
    except FileNotFoundError:
        logging.error("Input file 'tasks.csv' not found.")
        return
    except Exception as e:
        logging.error(f"Error reading input file: {str(e)}")
        return

    list_tasks = list(zip(df['Task_Description']))
    list_result = []
    
    total_tasks = len(list_tasks)
    for index, (task_description,) in enumerate(list_tasks, 1):
        logging.info(f"Processing task {index} of {total_tasks}")
        print(f"Processing task {index} of {total_tasks}")
        start = datetime.now()
        task_details = generate_generic_response(client, task_description)
        if task_details:
            list_result.append((task_description, task_details))
        
        # Rate limiting
        end = datetime.now()
        sleep_time = max(20 - (end - start).total_seconds(), 0)
        if sleep_time > 0:
            logging.info(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)

    df_result = pd.DataFrame(list_result, columns=['Task_Description', 'Task_Details'])
    df_result.columns = [re.sub(r'\W+', '_', col.upper()) for col in df_result.columns]

    try:
        df_result.to_pickle('./RESULT_Tasks_Details.pkl', protocol=4)
        logging.info("Results saved successfully.")
    except Exception as e:
        logging.error(f"Error saving results: {str(e)}")
    
    logging.info(f"Processing complete. {len(list_result)} out of {len(list_tasks)} tasks processed successfully.")
    logging.info(f"Results saved to {DIR_RESULT} and RESULT_Tasks_Details.pkl")
    print(f"Processing complete. {len(list_result)} out of {len(list_tasks)} tasks processed successfully.")
    print(f"Results saved to {DIR_RESULT} and RESULT_Tasks_Details.pkl")

def main():
    client = setup_openai_api()
    process_tasks(client)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)
