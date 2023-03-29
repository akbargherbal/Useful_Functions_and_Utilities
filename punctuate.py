from rpunct import RestorePuncts
# The default language is 'english'
import pandas as pd

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


rpunct = RestorePuncts()
df = pd.read_pickle("IISS_CC.pkl")

df = df.dropna().reset_index(drop=True)


list_vid_id = df['URL'].tolist()
list_text = df.CC.tolist()

inputs = list(zip(list_vid_id, list_text))
# inputs = inputs[:2]

def punctuate_text(text):
    result = rpunct.punctuate(text)
    return result

result = []

counter = 0
for vid_id, text in inputs:
    start = time_now()
    print(f'Processing {vid_id}...')
    result.append((vid_id, punctuate_text(text)))
    counter += 1
    print(f'Finished {counter} of {len(inputs)}')
    finish = time_now()
    duration = finish - start
    # Duration in seconds
    duration_in_s = duration.total_seconds()
    duration_in_min = duration_in_s / 60
    print(f'Duration: {duration_in_min} minutes')

    print('--------------------')


df_result = pd.DataFrame(result, columns=['URL', 'CC'])
df_result.to_pickle('IISS_CC_punctuated.pkl', protocol=4)