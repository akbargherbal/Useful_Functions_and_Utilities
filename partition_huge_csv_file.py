# Using Dask Partition Huge CSV Files to Smaller Chunks;

import dask.dataframe as dd

def partition_csv(file_path, chunksize=10, folder='CSV_PARTS', index=False):
    df = dd.read_csv(file_path, encoding='utf-8')
    df = df.repartition(npartitions=chunksize)  # 10 is the number of chunks

    df.to_csv('CSV_PARTS/PART_01_*.csv', encoding='utf-8', index=index)




