import sys

sys.path.append("..")
import os.path
import time
import pandas as pd
from crowdrank import ranker


def main():
    '''Script to call crowdrank as simply as possible
    python crowdrank_simple.py "keyword"'''
    keyword = sys.argv[1]
    skip = not (len(sys.argv) > 2 and sys.arg[2] == 0)
    ranking_df = ranker.rank(keyword, skip = skip)
    print(ranking_df)


if __name__ == "__main__":
    main()

