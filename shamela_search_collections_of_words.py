from collections import defaultdict, Counter
from itertools import chain
import pandas as pd
import regex as re
import os


from datetime import datetime
def time_now():
    '''Get Current Time'''
    
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    print("Current Time =", current_time)
    return now


############
print('Starting...')
start = time_now()
############

def make_ar_phrase_pattern(pat='token or more'):
    result = pat.split()
    result = [r'\S*'.join(word) for word in result]
    result = [fr'\S*{word}\S*' for word in result]
    result = fr'\s+'.join(result)
    result = fr"\S*{result}\S*"
    print(result)
    return result

def search_ar_books(pattern, max_results=100, books_list='List / Set of books'):
    # Initialize variables
    matches = []
    num_matches = 0
    result = []
    # Iterate over the books
    
    for (idx, book) in enumerate(books_list):
        print(f'''Searching {idx + 1} of {len(books_list)}:
{book} ... ''')
        with open(book, 'r', encoding='utf-8') as f:
            # Iterate over the lines in the book
            for line in f:
                # Check if the line matches the pattern
                if pattern.search(line):
                    # Add the match to the results
                    
                    matches = (line.strip())
                    result.append((book, matches))
                    num_matches += 1
                    # Check if we've found 100 matches
                    
                    if num_matches == max_results:
                        return result
        print(f'''Finished Searching {idx + 1} of {len(books_list)}:
{book}''')
        print('-'*50)
    # Return the matches
    return result


if __name__ == '__main__':

    pattern = input('Enter Pattern of Text to Search for:')
    reg_pat = re.compile(make_ar_phrase_pattern(pattern))



    path_to_books = input('Enter a path to the books dataframe; it should be a pickle file in the current directory: ')

    output_file = input('Enter a name for the output file: ')
    output_file = output_file.split('.pkl')[0]

    df_books = pd.read_pickle(path_to_books.strip())
    books_list = df_books.BOOK.tolist()
    books_list = books_list[:200]

    max_results = input('Enter the maximum number of results to be returned for each word/token: ')
    max_results = int(max_results)

    print(f'Number of books to be searched: {len(books_list)}')
    start = time_now()

    search_results = search_ar_books(pattern=reg_pat, books_list=books_list, max_results=max_results)

    end = time_now()
    duration_minutes = round(((end - start).total_seconds() / 60) , 2)
    print(f'Finished in {duration_minutes} minutes')


    df_search_results = pd.DataFrame(search_results).rename(columns={0: 'BOOK', 1: 'TEXT'})
    df_search_results.to_pickle(f'{output_file}.pkl', protocol=4)

    print('Done!')
