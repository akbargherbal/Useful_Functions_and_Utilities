#!/usr/bin/env python
# coding: utf-8

# HLPER FUNCTION: Get Time Now:
from datetime import datetime
def time_now():
    '''Get Current Time'''
    
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    print("Current Time =", current_time)
    return now



import os
from pathlib import Path

epub_dir = "placeholder"
p = Path(epub_dir)

while (p.exists() and p.is_dir()) == False:
    epub_dir = input(f"""
Please enter a valid Epub directory name!

""")
    epub_dir = epub_dir.strip()
    p = Path(epub_dir)
    
print("Epub directory is valid")

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='{asctime} {levelname:<8} {message}',
    style='{',
    filename=f'{epub_dir}_Converting_Novels_Epub_Using_Calibre_CLI.log',
    filemode='w')


import regex as re

import subprocess

from itertools import chain

from collections import Counter
# # Creating From EPUB to TXT Files Paths
list_from_to = []
for root, folders, files in os.walk(F'{epub_dir}/'):
    epub_files = [os.path.join(root, file) for file in files if file.endswith('.epub')]
    epub_files = sorted(epub_files)
    txt_files = [f"{file[:-5]}_CALIBCONV.txt" for file in epub_files]
    
    epub_files = [f'./{file}' for file in epub_files]
    txt_files = [f'./{file}' for file in txt_files]
    
    result = list(zip(epub_files, txt_files))
    list_from_to.append(result)

list_from_to = list(chain(*list_from_to))



# # Create Commands:
commands_list = [f"""
/home/jupyter/calibre-bin/calibre/ebook-convert
{file[0]}
{file[1]}
""".strip().split('\n')
for file in list_from_to
]

commands_list[0]

len(commands_list)


# # Executing Terminal Commands Using subprocess.Popen()



failed_processes = []
for (idx, command) in enumerate(commands_list):
    try:
        logging.debug(f"""
Starting Conversion: {str(idx+1).zfill(2)} of {len(commands_list)}
{command[1]}
EPUB File Size: {round(os.path.getsize(command[1]) / (1000 * 1000), 2)} MB
""".strip())
        start_process = time_now()
        subprocess.run(command)
        end_process = time_now()
        duration = end_process - start_process
        duration = duration.seconds
        logging.debug(f"""
Finished Converting {str(idx+1).zfill(2)} of {len(commands_list)}    
Duration: {duration}
{command[1]}
-------------------------------------------------------------
""".strip())

    except:
        failed_processes.append((command))
        logging.debug(f"""
The Following Process Failed:
##{command}##
-------------------------------------------------------------
""".strip())
6
with open('FAILED_PROCESSES.txt', encoding='utf-8', mode='w+') as file_failures:
    for failure in failed_processes:
        file_failures.write(f'{failure}\n')


len(commands_list)



