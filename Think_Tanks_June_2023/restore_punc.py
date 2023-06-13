import pandas as pd
from datetime import datetime


# Create a log file (overwrite if existing)
log_file = open('script_log.txt', 'w')

try:
    sample_size = int(input('Enter sample size: '))
except Exception as e:
    print(e)
    print('Defaulting to 1000 rows.')
    sample_size = 1000

rows_per_hr = 3000

est_duration = round(sample_size / rows_per_hr, 3)

print(f'Estimated duration: {est_duration} hours')
log_file.write(f'Estimated duration: {est_duration} hours\n')
print(f'Sample size: {sample_size}')



log_file.write(f'Sample size: {sample_size}\n')

print('Loading data...')
log_file.write('Loading data...\n')
df = pd.read_pickle('THINK_TANKS_DF_350K_ROWS.pkl').sample(sample_size)

print('Data loaded.')
log_file.write('Data loaded.\n')
df = df.reset_index(drop=True)

from rpunct import RestorePuncts
# The default language is 'english'
rpunct = RestorePuncts()

start = datetime.now()
log_file.write(f'Start time: {start}\n')

def restore_punc(text):
    try:
        result = rpunct.punctuate(text)
        return result
    except Exception as e:
        log_file.write(f'Error: {e}\n')
        return f'ERROR_PUNC {text}'

result = []

for i, text in enumerate(df['TEXT'], start=1):
    result.append(restore_punc(text))
    
    # Log progress every 1000 rows
    if i % 1000 == 0:
        log_file.write(f'Processed {i} rows\n')

df_punc = pd.DataFrame(data={'TEXT_PUNC': result})

df_punc.to_pickle(f'THINK_TANKS_DF_SAMPLE_{sample_size}_ROWS_PUNC.pkl', protocol=4)

end = datetime.now()
duration = end - start

log_file.write(f'End time: {end}\n')
log_file.write(f'Duration: {duration}\n')

print(f'Duration: {duration}')

# Close the log file
log_file.close()
