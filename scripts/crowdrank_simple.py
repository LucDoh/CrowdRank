import sys
sys.path.append("..")
import os.path
import time
import pandas as pd
from crowdrank import ranker

def main():
    keyword = sys.argv[1]
    ranking_df = ranker.rank(keyword)
    print(ranking_df)

if __name__ == '__main__':
    main()