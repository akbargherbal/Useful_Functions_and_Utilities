import regex as re
from collections import Counter
from itertools import chain
import pandas as pd
import os
import fasttext

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


words_set = input('Enter the path to the words set: ')


model = fasttext.load_model('08_50_39_ar_ft_dataset_500ngram_vec300.bin')
df_words_set = pd.read_pickle(words_set)

# Number of words:
words_set = list(set(df_words_set.WORD.to_list()))
print(f'Number of words: {len(words_set)}')

print('Creating a dictionay of word neighbours')


dict_word_neighbours_2000 = {}

for (idx , word) in enumerate(words_set):
    try:
        if idx % 1000 == 0:
            print(f'Procesing Word number: {idx}')
            time_now()
            print('---------------')
        dict_word_neighbours_2000[word] = model.get_nearest_neighbors(word)
    except:
        print(f'Error in word: {word}')
        continue



dict_word_neighbours_2000 = {k:[i[1] for i in v] for k,v in dict_word_neighbours_2000.items()}
print('Finished making a  dictionay of word neighbours')

df_words_and_neighbours = pd.DataFrame(dict_word_neighbours_2000.items(), columns=['WORD', 'NEIGHBOURS'])

# Save to pickle
df_words_and_neighbours.to_pickle('Poets_Gate_25_MARCH_2023/df_words_and_neighbours.pkl', protocol=4)


end = time_now()

duration = end - start
# Duration in Minutes:
print(f'Duration: {duration.seconds/60} minutes')


# def compare_similarity(ngram_1, ngram_2):
#     ngram_1 = ngram_1.split()
#     ngram_2 = ngram_2.split()
#     set_01 = [dict_word_neighbours_2000.get(i) for i in ngram_1]
#     set_02 = [dict_word_neighbours_2000.get(i) for i in ngram_2]
#     result = list(zip(set_01, set_02))
#     result = max(tuple(len(set(i[0]) - set(i[1])) for i in result))
#     return result
# df_bigram['SIM_FACTOR'] = df_bigram.apply(
# lambda x: compare_similarity(x['CANDIDATE_X'], x['BIGRAM']), axis=1
# )


# # df_bigram[df_bigram.SIM_FACTOR < 10]
# df_bigram.to_pickle('Poets_Gate_Text_march_2023/df_bi_count_stage_07.pkl', protocol=4)