import json
import requests
import spacy
import nltk
from collections import Counter
import sys

def get_assoc_comments(d):
    ''' Using a submission JSON, return a new JSON of all comments.'''
    c_page = requests.get('https://api.pushshift.io/reddit/submission/comment_ids/{}'.format(d['id']))
    c_data = json.loads(c_page.text)
    
    cs_page = requests.get('https://api.pushshift.io/reddit/comment/search?ids={}'.format(",".join(c_data['data'])))
    cs_data = json.loads(cs_page.text)
    
    return(cs_data['data'])

def get_and_dump(subreddit, num_posts, lookback_days = 360, dumppath = '../data/'):
    print("Looking at {}".format(subreddit))
    h_page = requests.get('http://api.pushshift.io/reddit/search/submission/?subreddit={}&q=best+advice+recommendations&before={}d&size={}'.format(subreddit,lookback_days, num_posts))
    
    # TBA: Put all this data on S3
    # Save submissions for later
    out_file = dumppath + "{}/{}_{}.{}".format("submission_data", subreddit, lookback_days, "json")
    submissions_data = json.loads(h_page.text)
    with open(out_file, 'w') as f:
        json.dump(submissions_data, f)


    comment_list = []
    # Iterate thru submissions, get associated comments
    for h_d in submissions_data['data']:
        comments = get_assoc_comments(h_d)
        comment_list.append(comments)
    
    # Save comment data
    out_file = dumppath + "{}/{}_{}.{}".format("comment_data", subreddit, lookback_days, "json")
    with open(out_file, 'w') as f:
        json.dump(comment_list, f)
    
    return out_file


def get_recent_posts(subreddits, num_posts = 500):
    for sr in subreddits:
        print("For {}, comments in {}".format(sr, get_and_dump(sr, num_posts)))


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
