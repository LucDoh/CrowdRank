import json
import requests
import spacy
import nltk
from collections import Counter
import sys
import os.path
import boto3
from . import helpers
# Functions for querying Pushshift.io API for relevant submissions,
# and storing all associtaed comments


class DataHandler():
    '''Data-handling class. Attributes are parameters about the 
    search (input and inferred) and data (comments, submissions),'''
    def __init__(self, keyword, num_posts, skip = True, use_s3 = False, lookback_days = 360):
        self.keyword = keyword.capitalize()
        self.num_posts = num_posts
        self.lookback = lookback_days
        self.skip = skip
        self.use_s3 = use_s3
        self.subreddits = self.keyword_to_subreddits()
        self.submissions = []
        self.comments = []
        self.comment_data = []
    
    def __str__(self): 
       return 'DH --> Keyword: \'{}\', subreddits: {}, num_posts: {}, use_s3: {}'.format(self.keyword, self.subreddits, self.lookback, self.num_posts, self.use_s3)
    
    def get_recent_posts(self):
        for sr in self.subreddits:
            if self.skip and check_for_comments(sr, self.use_s3):
                print("Using exists data for {}".format(sr))
                comments = [[]]
            else:
                print("Collecting new data for {}... Patientez ...".format(sr))
                comment_file, comments = get_and_dump(sr, self.num_posts, self.keyword, self.lookback, self.use_s3)
                print(
                    "For {}, comments in {}".format(sr, comment_file)
                )
        self.comments = helpers.unpack_comments(comments)
        return self.comments
        

    def keyword_to_subreddits(self):
    # For each keyword (electronics category) top 
    # 1-3 subreddits. Later: generalize this
    # (Topic modeling of subreddits + similarity to word
    # reprs).
        kw_subreddit = {
            "Headphones": ["headphoneadvice"],
            "Laptops": ["laptops", "suggestalaptop", "laptopdeals", "macbook"],
            "Computers": ["computers", "suggestapc", "pcmasterrace"],
            "Keyboards": ["mechanicalkeyboards", "keyboards", "mechanicalkeyboardsUK"],
            "Mouses": ["MouseReview"],
            "Monitors": ["Monitors"],
            "Tvs": ["Televisions"],
            "Tablets": ["Tablets", "androidtablets", "ipad"],
            "Smartwatches": ["smartwatch", "androidwear", "ioswear"],
        }

        if not self.keyword in kw_subreddit:
            print("None found, using BuyItForLife")
            return "BIFL"
        return kw_subreddit[self.keyword]



def get_and_dump(subreddit, num_posts, keyword, lookback_days=360, use_s3 = False):
    print("Looking at {}".format(subreddit))
    h_page = requests.get(
        "http://api.pushshift.io/reddit/search/submission/?subreddit={}&q=best+advice+recommendations&before={}d&size={}&sort_type=score".format(
            subreddit, lookback_days, num_posts
        )
    )

    # Get all relevant submissions, verify subreddit
    submissions_data = json.loads(h_page.text)
    submission_ids = get_submission_ids(submissions_data["data"], subreddit)
    print("Submissions from {}: {} ({})".format(subreddit, len(submission_ids), len(submissions_data['data'])))
    # Iterate thru submissions, get associated comments
    comment_list = []
    for submission_id in submission_ids:
        comments = get_assoc_comments(submission_id)
        comment_list.append(comments)

    # Save submissions for later
    posts = (submissions_data["data"], comment_list)

    if use_s3:
        comment_file = save_posts_to_S3(posts, subreddit, lookback_days)
    else:
        comment_file = save_posts_locally(posts, subreddit, lookback_days)

    return comment_file, comment_list



def get_assoc_comments(subm_id):
    """ For a submission ID, request a JSON of associated comments."""
    cs_page = requests.get(
        "https://api.pushshift.io/reddit/search/comment/?link_id={}".format(subm_id)
    )

    comments = json.loads(cs_page.text)["data"]
    return comments


def get_submission_ids(combined_submissions, subreddit):
    """ Get submission ids, remove duplicates, verify subreddit """
    submission_ids = [
        sub["id"]
        for sub in combined_submissions
        if sub["subreddit"].lower() == subreddit.lower()
    ]
    submission_ids = list(set(submission_ids))
    return submission_ids


def save_posts_locally(posts, subreddit, lookback_days, dumppath="../data/"):
    # Save submissions & comments for later
    out_file = dumppath + "{}/{}_{}.json".format(
        "submission_data", subreddit, lookback_days
    )
    with open(out_file, "w") as f:
        json.dump(posts[0], f)

    out_file = dumppath + "{}/{}_{}.json".format(
        "comment_data", subreddit, lookback_days
    )
    with open(out_file, "w") as f:
        json.dump(posts[1], f)

    return out_file


def save_posts_to_S3(posts, subreddit, lookback_days, bucket_name = 'crowdsourced-data-reddit'):
    # Save posts to S3
    file_name = "{}/{}_{}.{}".format(
        "submission_data", subreddit, lookback_days, "json")
    helpers.save_json_to_S3(posts[0], bucket_name, file_name)

    file_name = "{}/{}_{}.{}".format(
        "comment_data", subreddit, lookback_days, "json")
    helpers.save_json_to_S3(posts[1], bucket_name, file_name)

    return "{}/{}".format(bucket_name, file_name)


def check_for_comments(subreddit, use_s3, lookback_days=360):
    # True iff a corresponding comments file exists
    cmt_file = "{}/{}_{}.{}".format(
        "comment_data", subreddit, lookback_days, "json"
    )
    if use_s3:
        return helpers.check_for_data_S3(cmt_file)
    else:
        return os.path.isfile("../data/" + cmt_file)
