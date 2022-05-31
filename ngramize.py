def ngramize(x, n=3):
    x = x.split()
    return [
    ' '.join(x[i:i+n] )
    for i in range(
    len(x)-n+1
    )
        ]