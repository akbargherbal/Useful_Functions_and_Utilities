'''
Split a a pandas a huge dataframe df into 10 smaller dataframes; df1, df2, df3, ..., df so that each dataframe is less than 10000 rows.
'''
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

df = pd.read_csv('data.csv')
df = df.drop(columns=['Unnamed: 0'])
df = df.dropna()

df1, df2, df3, df4, df5, df6, df7, df8, df9, df10 = np.array_split(df, 10)

df1.to_csv('data1.csv')
df2.to_csv('data2.csv')
df3.to_csv('data3.csv')
df4.to_csv('data4.csv')
df5.to_csv('data5.csv')
df6.to_csv('data6.csv')
df7.to_csv('data7.csv')
df8.to_csv('data8.csv')
df9.to_csv('data9.csv')
df10.to_csv('data10.csv')
'''