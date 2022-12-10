'''
Convert a pandas DataFrame of word vs. frequency to a python class.
'''

class DataFrameToClass:
    def __init__(self, df):
        self.df = df
        print(f'''
DataFrameToClass initialized
The columns in the DataFrame are: {self.df.columns}
'''.strip())

    def to_dict(self, key, value):
        return self.df.set_index(key)[value].to_dict()

    def count_values_by_column(self, column):
        return self.df[column].value_counts().to_dict()

