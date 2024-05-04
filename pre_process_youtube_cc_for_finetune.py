import pandas as pd
from itertools import chain
from collections import Counter

def read_and_process_data(file_path):
    """
    Read a DataFrame from a pickle file and perform initial data processing.
    
    Parameters:
    - file_path (str): Path to the pickle file.
    
    Returns:
    - DataFrame: Processed DataFrame.
    """
    df = pd.read_pickle(file_path)
    df['INDEX'] = df.index
    df['LEN'] = df['text'].apply(lambda x: len(x.split()))
    df['text'] = df['text'].apply(sub_filler)
    return df

def sub_filler(x):
    """
    Replace '[music]' with '...' in a string.
    
    Parameters:
    - x (str): Input string.
    
    Returns:
    - str: Processed string.
    """
    if x.lower().strip() == '[music]':
        return '...'
    else:
        return x

def group_texts_by_bin(df, max_len=2500):
    """
    Group texts by bins based on cumulative length.
    
    Parameters:
    - df (DataFrame): Input DataFrame.
    - max_len (int): Maximum length for each bin.
    
    Returns:
    - DataFrame: DataFrame grouped by bins.
    """
    df['CUM_LEN'] = df.LEN.cumsum()
    df['BIN'] = df.CUM_LEN.apply(lambda x: x // max_len)
    df['IDX_TEXT'] = pd.Series(list(zip(df.INDEX , df.text)))
    df = df.groupby(['BIN'], as_index=False).agg({'IDX_TEXT': lambda x: x.to_list()})
    df['IDX_TEXT'] = df['IDX_TEXT'].apply(lambda x: custom_sort(x, 0))
    df['TEXT'] = df['IDX_TEXT'].apply(lambda x: ' '.join([i[1] for i in x]))
    return df

def custom_sort(lst, idx):
    """
    Custom sorting function to sort a list of tuples by a specific index.
    
    Parameters:
    - lst (list): Input list of tuples.
    - idx (int): Index to sort by.
    
    Returns:
    - list: Sorted list of tuples.
    """
    return sorted(lst, key=lambda x: x[idx])
