import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
import logging
import time

# Configure logging
TIME_STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
log_file = f"LOG_{TIME_STAMP}.log"
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w',
    filename=log_file,
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Directories
input_dir = input('Enter the directory path containing epub files: ')
output_dir = input('Enter the output directory path for txt files: ')

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Function to convert EPUB to TXT using Calibre's ebook-convert tool
def convert_epub_to_txt(epub_path, txt_path):
    try:
        start_time = time.time()
        # Call the ebook-convert command
        subprocess.run(['ebook-convert', epub_path, txt_path], check=True)
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Converted: {epub_path} to {txt_path} in {duration:.2f} seconds")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error converting {epub_path}: {e}")

# Function to process a single file
def process_file(file_name):
    if file_name.endswith('.epub'):
        epub_path = os.path.join(input_dir, file_name).replace('\\', '/')
        txt_path = os.path.join(output_dir, os.path.splitext(file_name)[0] + '.txt').replace('\\', '/')
        convert_epub_to_txt(epub_path, txt_path)

# Get all EPUB files in the input directory
epub_files = [file for file in os.listdir(input_dir) if file.endswith('.epub')]

# Use ProcessPoolExecutor to convert files concurrently
with ProcessPoolExecutor() as executor:
    executor.map(process_file, epub_files)

logging.info("Conversion process completed.")
