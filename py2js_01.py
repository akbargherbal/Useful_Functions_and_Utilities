quiz_set = [
    {'Q': 'question 1', 'list_options': ['A', 'BN', 'C', 'D']},
    {'Q': 'question 2', 'list_options': ['z', 'B', 'd', 'D']},
    {'Q': 'question 3', 'list_options': ['bda', 'B', 'dfd', 'D']},
    {'Q': 'question 4', 'list_options': ['dfd', 'B', 'C', 'D']},
]

correct = 0
wrong = 0
finished = 0
while len(quiz_set) > 0 :
    quiz = quiz_set.pop(0)
    question = quiz['Q']
    options = quiz['list_options']
    answer = input(f'{question}\n').strip()
    if answer in options:
        correct += 1
    else:
        wrong += 1
    finished += 1