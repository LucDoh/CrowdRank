import json
import requests
import spacy
import nltk
from collections import Counter
import sys
import os.path

# Functions for querying Pushshift.io API for relevant submissions,
# and storing all associtaed comments


def get_assoc_comments(subm_id):
    """ For a submission ID, request a JSON of associated comments."""
    # Double check this fix works (only picking up comments in the correct
    # subreddits)

    """c_page = requests.get(
        "https://api.pushshift.io/reddit/submission/comment_ids/{}".format(subm_id)
    )
    c_data = json.loads(c_page.text)
    # Maximum of 25.
    cs_page = requests.get(
        "https://api.pushshift.io/reddit/comment/ids={}".format(
            ",".join(c_data["data"])
        )
    )"""

    cs_page = requests.get(
        "https://api.pushshift.io/reddit/search/comment/?link_id={}".format(subm_id)
    )

    comments = json.loads(cs_page.text)["data"]
    #print(cs_page.text)
    #print(comments)
    return comments


def get_submission_ids(combined_submissions, subreddit):
    """ Get submission ids, rm duplicates, verify subreddit """
    submission_ids = [
        sub["id"]
        for sub in combined_submissions
        if sub["subreddit"].lower() == subreddit.lower()
    ]
    submission_ids = list(set(submission_ids))
    return submission_ids


def save_posts(posts, subreddit, lookback_days, dumppath="../data/"):
    # Save submissions & comments for later (TBD: S3)
    out_file = dumppath + "{}/{}_{}.{}".format(
        "submission_data", subreddit, lookback_days, "json"
    )
    with open(out_file, "w") as f:
        json.dump(posts[0], f)

    out_file = dumppath + "{}/{}_{}.{}".format(
        "comment_data", subreddit, lookback_days, "json"
    )
    with open(out_file, "w") as f:
        json.dump(posts[1], f)

    return out_file

 
def is_ec2():
    # Check if on EC2 (not local)
    import socket
    try:
        socket.gethostbyname('instance-data.ec2.internal.')
        return True
    except socket.gaierror:
        return False

def bucket_exists():
    # Check that main bucket exists
    import boto3
    s3 = boto3.resource('s3')
    return s3.Bucket('crowdsourced-data-reddit') in s3.buckets.all()


def get_and_dump_expanded(
    subreddit, num_posts, keyword, lookback_days=360, dumppath="../data/"
):
    """ Expansive search: do separate queries for keyword + advice_synonym,
    then add the results. In testing, this gets about 5x submissions."""
    print("Looking at {}".format(subreddit))

    best_page = requests.get(
        "http://api.pushshift.io/reddit/search/submission/?subreddit={}&q={}+recommendations&before={}d&size={}&sort_type=score".format(
            subreddit, keyword, lookback_days, num_posts
        )
    )
    recc_page = requests.get(
        "http://api.pushshift.io/reddit/search/submission/?subreddit={}&q={}+advice&before={}d&size={}&sort_type=score".format(
            subreddit, keyword, lookback_days, num_posts
        )
    )
    advice_page = requests.get(
        "http://api.pushshift.io/reddit/search/submission/?subreddit={}&q={}+best&before={}d&size={}&sort_type=score".format(
            subreddit, keyword, lookback_days, num_posts
        )
    )

    submissions_data_best = json.loads(best_page.text)
    submissions_data_recc = json.loads(recc_page.text)
    submissions_data_advice = json.loads(advice_page.text)

    combined_submissions = (
        submissions_data_best["data"]
        + submissions_data_recc["data"]
        + submissions_data_advice["data"]
    )
    print(combined_submissions)
    # Get all submission ids, and double check the subreddit is correct
    submission_ids = get_submission_ids(combined_submissions, subreddit)

    comment_list = []
    for submission_id in submission_ids:
        comment_list.append(get_assoc_comments(submission_id))
    #print(submission_ids)
    #print(comment_list)
    # Save submissions for later
    posts = (combined_submissions, comment_list)
    comment_file = save_posts(posts, subreddit, lookback_days, dumppath="../data/")
    return comment_file, comment_list


def get_and_dump(subreddit, num_posts, keyword, lookback_days=360, dumppath="../data/"):
    print("Looking at {}".format(subreddit))
    h_page = requests.get(
        "http://api.pushshift.io/reddit/search/submission/?subreddit={}&q=best+advice+recommendations&before={}d&size={}&sort_type=score".format(
            subreddit, lookback_days, num_posts
        )
    )

    # Get all relevant submissions, verify subreddit
    submissions_data = json.loads(h_page.text)
    submission_ids = get_submission_ids(submissions_data["data"], subreddit)

    # Iterate thru submissions, get associated comments
    comment_list = []
    for submission_id in submission_ids:
        comments = get_assoc_comments(submission_id)
        comment_list.append(comments)

    # Save submissions for later
    posts = (submissions_data["data"], comment_list)
    comment_file = save_posts(posts, subreddit, lookback_days, dumppath)

    return comment_file, comment_list


def check_for_comments(subreddit, lookback_days=360):
    # True iff a corresponding comments file exists
    cmt_file = "../data/{}/{}_{}.{}".format(
        "comment_data", subreddit, lookback_days, "json"
    )
    return os.path.isfile(cmt_file)


def count_comments(sr, lookback_days):
    # Get number comments stored in 2D list
    comments_path = "../data/comment_data/{}_{}.json".format(sr, lookback_days)
    with open(comments_path) as f:
        comments_2D = json.load(f)
    return sum([len(comments) for comments in comments_2D])


def keyword_to_subreddits(keyword):
    """For a keyword (electronics category), return the top 
    1-3 subreddits for it. In the future, this could be generalized
    by an NLP model (Topic modeling of subreddits + similarity of word
    representations). """
    kw_to_subreddits = {
        "Headphones": ["headphoneadvice"],
        "Laptops": ["laptops", "suggestalaptop", "laptopdeals"],
        "Computers": ["computers", "suggestapc", "pcmasterrace"],
        "Keyboards": ["mechanicalkeyboards", "keyboards", "mechanicalkeyboardsUK"],
        "Mouses": ["MouseReview"],
        "Monitors": ["Monitors"],
        "Tvs": ["Televisions"],
        "Tablets": ["Tablets", "androidtablets", "ipad"],
        "Smartwatches": ["smartwatch", "androidwear", "ioswear"],
    }

    return kw_to_subreddits[keyword]


def get_recent_posts(keyword, num_posts=500, skip=True):
    """ Maps keyword to subreddits, queries pushshift.io to
    get submissions in the last year, gets associated comments,
    and saves compressed comment data."""

    subreddits = keyword_to_subreddits(keyword)
    for sr in subreddits:
        print("Checking if comments exist for {}".format(sr))
        if skip and not check_for_comments(sr):
            print(
                "For {}, comments in {}".format(
                    sr, get_and_dump(sr, num_posts, keyword)[0]
                )
            )

    return subreddits
