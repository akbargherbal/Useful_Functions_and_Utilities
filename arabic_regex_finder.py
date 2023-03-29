import regex as re

def make_ar_phrase_pattern(pat='token or more'):
    result = pat.split()
    result = [r'\S*'.join(word) for word in result]
    result = [fr'\S*{word}\S*' for word in result]
    result = fr'\s+'.join(result)
    result = fr"\S*{result}\S*"
    print(result)
    return result