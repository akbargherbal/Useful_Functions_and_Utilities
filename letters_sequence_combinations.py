from itertools import permutations, combinations
import pandas as pd

def get_seq_combination(word, n):
    
    if len(word) <= n:
        return [word]
    
    word_01 = list(combinations(list(range(len(word))), n))
    word_01 = pd.DataFrame(word_01)

    list_idx = list(range(n))

    list_idx = list(combinations(list_idx, 2))


    cond = [word_01[i] < word_01[j] for i,j in list_idx]

    cond_exp = '&'.join([f'cond[{i}]' for i in list(range(len(cond)))])

    word_01 =  word_01[eval(cond_exp)].reset_index(drop=True)
    
    list_col = word_01.columns.tolist()

    word_01 = list(zip(*[word_01[i] for i in list_col]))
    word_01 = [''.join([word[i] for i in j]) for j in word_01]
    
    return word_01