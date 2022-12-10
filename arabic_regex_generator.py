import regex as re
from itertools import chain
from collections import Counter

def ar_regex_generator(tokens_sequence="sequence of tokens", output_file= 'regex_output_file'):
  """
  Enter a sequence of tokens
  """.strip()

  tokens_sequence = input(f"""
Enter Words Sequence:
  
  """.strip())

  input_data = tokens_sequence
  tokens_sequence = [i.strip() for i in tokens_sequence.strip().split()]


  tokens_sequence = [fr"\w*?".join(token) for token in tokens_sequence ]
  tokens_sequence = [fr"\w*?{token}\w*?" for token in tokens_sequence ]

  print(f"After Embedding Letters: {tokens_sequence}")

  # tokens_sequence = [fr"\b{token}\b" for token in tokens_sequence ]
  # print(f"After Embedding Boundary: {tokens_sequence}")

  tokens_sequence = fr'\s*?'.join(tokens_sequence)
  print(f"After Embedding SPACE: {tokens_sequence}")

  #tokens_sequence = re.sub(r'[\\]{2,}', r'\\', tokens_sequence)

  with open(f'{output_file}.txt', encoding='utf-8', mode='+a') as f:
      f.write(f"{input_data}\t.......\t{tokens_sequence}\n")


  print(f'Regex Pattern can be found in {output_file}.txt')
  return tokens_sequence

ar_regex = ar_regex_generator()