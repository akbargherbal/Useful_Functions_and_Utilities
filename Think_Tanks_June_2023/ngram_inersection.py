import regex as re
import pandas as pd
import time
import logging
from itertools import chain
from collections import Counter

# Set up logging
logging.basicConfig(filename='log_file.log', level=logging.INFO, format='%(asctime)s - %(message)s')

df = pd.read_pickle('THINK_TANKS_DF_SAMPLE_50000_ROWS_PUNC.pkl')

pat_punc = ',.!;?:'
pat_punc = f'[{pat_punc}]'
pat_punc = re.compile(pat_punc)
df['TEXT'] = df.TEXT_PUNC.apply(lambda x: pat_punc.split(x))
df = df[['TEXT']]
df = df.explode(['TEXT']).reset_index(drop=True)

df = df[df['TEXT'].str.len() > 1]
df['TEXT'] = df['TEXT'].str.lower()
df = df.reset_index(drop=True)

logging.info(f'Total number of Rows: {len(df)}')

df['LEN'] = df['TEXT'].apply(lambda x: len(x.split()))
df = df[df['LEN']> 2]
df = df[df['LEN']< 100]
df = df.reset_index(drop=True)

df_ngram = pd.read_pickle('THINK_TANKS_COMBINED_BATCHES_ALL_PATTERNS_STAGE_12.pkl')
ngram_set = set(i.lower() for i in (df_ngram.TEXT_PAT.tolist()))

def preprocess_text(df):
    df['TEXT'] = df['TEXT'].str.lower()  # Convert text to lowercase
    return df

def construct_pattern(ngram_set):
    pattern = re.compile(fr'\b(?:{"|".join(ngram_set)})\b')  # Compile the regex pattern
    return pattern

def find_ngrams(text, pattern):
    ngrams = set(pattern.findall(text))  # Use the precompiled pattern
    return ngrams

def add_ngram_column(df, ngram_set):
    df = preprocess_text(df)
    total_rows = len(df)
    ngram_column = [None] * total_rows  # Preallocate the list
    pattern = construct_pattern(ngram_set)

    start_time = time.time()

    for i, text in enumerate(df['TEXT']):
        ngrams = find_ngrams(text, pattern)
        ngram_column[i] = ngrams

        if (i + 1) % (total_rows // 10) == 0:
            progress = (i + 1) / total_rows * 100
            duration = time.time() - start_time
            logging.info(f"Progress: {progress:.1f}% | Duration: {duration:.2f} seconds")

    df['NGRAM'] = ngram_column
    return df

# Call the add_ngram_column function with the preprocessed data
df = add_ngram_column(df, ngram_set)
df.to_pickle('THINK_TANK_NGRAM_INTERSECTION_STAGE_01.pkl', protocol=4)
