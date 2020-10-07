import json
import requests
import spacy
import nltk
from collections import Counter
import sys


# Ingestion handler object would make this cleaner.

def get_assoc_comments(d):
    ''' Using a submission JSON, return a new JSON of all comments.'''
    c_page = requests.get('https://api.pushshift.io/reddit/submission/comment_ids/{}'.format(d['id']))
    c_data = json.loads(c_page.text)
    
    cs_page = requests.get('https://api.pushshift.io/reddit/comment/search?ids={}'.format(",".join(c_data['data'])))
    cs_data = json.loads(cs_page.text)
    
    return(cs_data['data'])

def get_and_dump(subreddit, num_posts, lookback_days = 360, dumppath = '../data/'):
    print("Looking at {}".format(subreddit))
    h_page = requests.get('http://api.pushshift.io/reddit/search/submission/?subreddit={}&q=best+advice+recommendations&before={}d&size={}&sort_type=score'.format(subreddit,lookback_days, num_posts))
    
    # TBD: Put all this data on S3
    # Save submissions for later
    out_file = dumppath + "{}/{}_{}.{}".format("submission_data", subreddit, lookback_days, "json")
    submissions_data = json.loads(h_page.text)
    with open(out_file, 'w') as f:
        json.dump(submissions_data, f)


    # Iterate thru submissions, get associated comments
    comment_list = []
    for h_d in submissions_data['data']:
        comments = get_assoc_comments(h_d)
        comment_list.append(comments)
    
    # Save comment data
    out_file = dumppath + "{}/{}_{}.{}".format("comment_data", subreddit, lookback_days, "json")
    with open(out_file, 'w') as f:
        json.dump(comment_list, f)
    
    return out_file

    

def keyword_to_subreddits(keyword):
    '''For a keyword (electronics category), return the top 
    1-3 subreddits for it. In the future, this would be done by
    a model (compare similarity of keyword to subreddit description) 
    so it generalizes. For now, just support these.'''
    kw_to_subreddits = { 
    'Headphones': ['headphoneadvice', 'audiophile', 'budgetaudiophile'],
    'Laptops': ['laptops', 'suggestalaptop', 'laptopdeals'],
    'Computers': ['computers', 'suggestapc', 'pcmasterrace'],
    'Keyboards': ['mechanicalkeyboards', 'keyboards', 'mechanicalkeyboardsUK'],
    'Mouses' : ['MouseReview'],
    'Monitors': ['Monitors'],
    'Tvs' : ['Televisions'],
    'Tablets': ['Tablets', 'androidtablets', 'ipad'],
    'Smartwatches' : ['smartwatch', 'androidwear', 'ioswear']
    }

    return kw_to_subreddits[keyword]

'''def get_recent_posts(subreddits, num_posts = 500):
    for sr in subreddits:
        print("For {}, comments in {}".format(sr, get_and_dump(sr, num_posts)))'''

def get_recent_posts(keyword, num_posts = 500):
    # Supports keyword --> multiple subreddits
    subreddits = keyword_to_subreddits(keyword)
    for sr in subreddits:
        print("For {}, comments in {}".format(sr, get_and_dump(sr, num_posts)))
    return subreddits

def main():
    ''' Taking in 3 subreddits, this script queries pushshift.io 
    to get submissions in the last year, gets associated comments,
    and saves these to files on a per-subreddit basis.'''
    subreddit_list = sys.argv[1], sys.argv[2], sys.argv[3]
    
    # TBA: Parallelize
    sr = sys.argv[1]

    get_and_dump(sr)
    #get_comments_save(subreddit_list)

if __name__=="__main__":
    main()
