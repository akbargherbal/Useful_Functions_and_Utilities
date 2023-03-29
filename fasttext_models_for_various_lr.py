from datetime import datetime
import os
import regex as re
import logging
import fasttext
from collections import Counter
from itertools import chain
import pandas as pd

def time_now():
    '''Get Current Time'''
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    print("Current Time =", current_time)
    return now

print('Starting...')
start = time_now()

logging.basicConfig(format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

vector_size = 50
window_size = 5
min_count = 5
epochs = 5
maxn = 4
minn = 3

hr_min_sec = start.strftime("%H_%M_%S")
output_folder = 'fasttext_models_vec50'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for learning_rate in [0.1, 0.075, 0.05, 0.025]:
    dict_01 = {
        'vector_size': vector_size,
        'window_size': window_size,
        'min_count': min_count,
        'learning_rate': learning_rate,
        'epochs': epochs,
        'maxn': maxn,
        'minn': minn,
    }
    print(dict_01)

    output_file = f'{hr_min_sec}_ar_ft_dataset_500ngram_vec{vector_size}_maxn{maxn}_minn{minn}_LR{learning_rate}.bin'
    print(f'OUTPUT FILE NAME IS: {output_file}')
    logger.info(f'{output_file}')
    logger.info('----------------------')

    ar_model = fasttext.train_unsupervised(
        'Poets_Gate_Text_march_2023/poems_pp_500.txt', model='skipgram',
        dim=vector_size, ws=window_size, minCount=min_count, lr=learning_rate, epoch=epochs,
        maxn=maxn, minn=minn)

    ar_model.save_model(os.path.join(output_folder, output_file))

    hyperparameters = {
        'dim': ar_model.f.getArgs().dim,
        'ws': ar_model.f.getArgs().ws,
        'minCount': ar_model.f.getArgs().minCount,
        'lr': ar_model.f.getArgs().lr,
        'epoch': ar_model.f.getArgs().epoch,
        'maxn': ar_model.f.getArgs().maxn,
        'minn': ar_model.f.getArgs().minn,
        'model': ar_model.f.getArgs().model
    }
    print('Hyperparameters used to train the model:')
    for key, value in hyperparameters.items():
        print(f"{key}: {value}")
