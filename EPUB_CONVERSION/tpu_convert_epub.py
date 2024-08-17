import os
import subprocess
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
import time
import psutil
import traceback
import sys

# Configure logging
TIME_STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
log_file = f"ebook_conversion_LOG_{TIME_STAMP}.log"
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add a file handler to write logs to a file
file_handler = logging.FileHandler(log_file, mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

# Flush handler after each log
class FlushingStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

stream_handler = FlushingStreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(stream_handler)

# Directories
input_dir = input('Enter the directory path containing epub files: ')
output_dir = input('Enter the output directory path for txt files: ')

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Global variables
file_queue = queue.Queue()
total_cores = psutil.cpu_count(logical=True)
max_workers = int(total_cores * 0.8)  # Use 80% of available cores
current_workers = 0
worker_lock = threading.Lock()
successful_conversions = 0
failed_conversions = 0
conversion_lock = threading.Lock()

def convert_epub_to_txt(epub_path, txt_path):
    try:
        start_time = time.time()
        result = subprocess.run(['ebook-convert', epub_path, txt_path], 
                                check=True, capture_output=True, text=True)
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Converted: {epub_path} to {txt_path} in {duration:.2f} seconds")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error converting {epub_path}: {e}")
        logging.error(f"Subprocess output: {e.output}")
        logging.error(f"Subprocess stderr: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error converting {epub_path}: {e}")
        logging.error(traceback.format_exc())
        return False

def worker():
    global current_workers, successful_conversions, failed_conversions
    while True:
        try:
            file_name = file_queue.get(block=False)
        except queue.Empty:
            break

        if file_name.endswith('.epub'):
            epub_path = os.path.join(input_dir, file_name)
            txt_path = os.path.join(output_dir, os.path.splitext(file_name)[0] + '.txt')
            success = convert_epub_to_txt(epub_path, txt_path)
            with conversion_lock:
                if success:
                    successful_conversions += 1
                else:
                    failed_conversions += 1

        file_queue.task_done()

    with worker_lock:
        current_workers -= 1

def main():
    global current_workers, successful_conversions, failed_conversions
    start_time = time.time()

    try:
        # Populate the queue
        for file_name in os.listdir(input_dir):
            if file_name.endswith('.epub'):
                file_queue.put(file_name)

        total_files = file_queue.qsize()
        logging.info(f"Total files to process: {total_files}")
        print(f"Total files to process: {total_files}")

        # Create and start worker threads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while not file_queue.empty():
                with worker_lock:
                    if current_workers < max_workers:
                        executor.submit(worker)
                        current_workers += 1
                time.sleep(0.1)  # Small delay to prevent busy-waiting

        # Wait for all tasks to complete
        file_queue.join()

    except Exception as e:
        logging.error(f"An unexpected error occurred in the main process: {e}")
        logging.error(traceback.format_exc())
    finally:
        end_time = time.time()
        total_time = end_time - start_time

        logging.info(f"Conversion process completed in {total_time:.2f} seconds.")
        logging.info(f"Successfully converted: {successful_conversions}")
        logging.info(f"Failed conversions: {failed_conversions}")
        print(f"Total execution time: {total_time:.2f} seconds")
        print(f"Successfully converted: {successful_conversions}")
        print(f"Failed conversions: {failed_conversions}")

if __name__ == "__main__":
    main()