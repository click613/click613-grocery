
import json, os
def endings_share(prices, m):
    ok = 0
    for p in prices:
        c = round(p / m * 100)
        if c % 10 == 9 or c % 100 == 0 or c % 100 == 50: ok += 1
    return ok / len(prices) if prices else 0
def fit(prices, lo=1.0, hi=1.30, step=0.0025):
    res = []
    m = lo
    while m <= hi + 1e-9:
        res.append((round(m, 4), endings_share(prices, m))); m += step
    res.sort(key=lambda x: -x[1])
    return res
