import json
import requests
import spacy
import nltk
from collections import Counter
import sys
import os.path

# Ingestion: query Pushshift.io API for relevant submissions,
# then get all associated comments. Store this.


def get_assoc_comments(subm_id):
    """ Using a submission ID, return a new JSON of all comments."""
    # c_page = requests.get('https://api.pushshift.io/reddit/submission/comment_ids/{}'.format(d['id']))

    c_page = requests.get(
        "https://api.pushshift.io/reddit/submission/comment_ids/{}".format(
            subm_id)
    )
    c_data = json.loads(c_page.text)

    # Maximum of 25.
    cs_page = requests.get(
        "https://api.pushshift.io/reddit/comment/search?ids={}".format(
            ",".join(c_data["data"])
        )
    )
    cs_data = json.loads(cs_page.text)

    return cs_data["data"]

def get_submission_ids(combined_submissions, subreddit):
    # Get submission ids, rm duplicates, check subreddit is correct
    submission_ids = [sub["id"]
        for sub in combined_submissions
        if sub["subreddit"].lower() == subreddit.lower()
    ]
    submission_ids = list(set(submission_ids)) 
    return submission_ids


def get_and_dump_expanded(
    subreddit, num_posts, keyword, lookback_days=360, dumppath="../data/"
):
    """ Expanding the search, do 3 queries for keyword + advice_synonym
    and then add the results. Upon testing, this gets about 5x
    as many submissions."""
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

    # TBD: Put all this data on S3
    # Save submissions for later
    out_file = dumppath + "{}/{}_{}.{}".format(
        "submission_data", subreddit, lookback_days, "json"
    )
    with open(out_file, "w") as f:
        json.dump(combined_submissions, f)

    # Get all submission ids, and double check the subreddit is correct
    submission_ids = get_submission_ids(combined_submissions, subreddit)

    # Iterate thru submissions, get associated comments
    comment_list = []
    for submission_id in submission_ids:
        comments = get_assoc_comments(submission_id)
        comment_list.append(comments)

    # Save comment data
    out_file = dumppath + "{}/{}_{}.{}".format(
        "comment_data", subreddit, lookback_days, "json"
    )
    with open(out_file, "w") as f:
        json.dump(comment_list, f)

    return out_file


def get_and_dump(subreddit, num_posts, keyword, lookback_days=360, dumppath="../data/"):
    print("Looking at {}".format(subreddit))
    h_page = requests.get(
        "http://api.pushshift.io/reddit/search/submission/?subreddit={}&q=best+advice+recommendations&before={}d&size={}&sort_type=score".format(
            subreddit, lookback_days, num_posts
        )
    )

    # Get all relevant submissions
    submissions_data = json.loads(h_page.text)

    # Submission ids, double checking the subreddit is correct
    submission_ids = get_submission_ids(submissions_data['data'], subreddit)

    # Iterate thru submissions, get associated comments
    comment_list = []
    for submission_id in submission_ids:
        comments = get_assoc_comments(submission_id)
        comment_list.append(comments)


    # TBD: Put all this data on S3
    # Save submissions for later
    submission_file = dumppath + "{}/{}_{}.{}".format(
        "submission_data", subreddit, lookback_days, "json"
    )

    with open(submission_file, "w") as f:
        json.dump(submissions_data, f)

    # Save comment data
    comment_file = dumppath + "{}/{}_{}.{}".format(
        "comment_data", subreddit, lookback_days, "json"
    )
    with open(comment_file, "w") as f:
        json.dump(comment_list, f)

    return comment_file

def check_for_comments(subreddit, lookback_days = 360):
    # True if a corresponding comments file exists, else False
    cmt_file = "../data/{}/{}_{}.{}".format(
        "comment_data", subreddit, lookback_days, "json"
    )

    if os.path.isfile(cmt_file):
        return True
    else:
        return False



def count_comments(sr, lookback_days):
    # Gets num of comments in 2D list
    comments_path = "../data/comment_data/{}_{}.json".format(sr, lookback_days)
    with open(comments_path) as f:
        comments_2D = json.load(f)
    return sum([len(comments) for comments in comments_2D])


def keyword_to_subreddits(keyword):
    """For a keyword (electronics category), return the top 
    1-3 subreddits for it. In the future, this would be done by
    a model (compare similarity of keyword to subreddit description) 
    so it generalizes. For now, just support these."""
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


"""def get_recent_posts(subreddits, num_posts = 500):
    for sr in subreddits:
        print("For {}, comments in {}".format(sr, get_and_dump(sr, num_posts)))"""


def get_recent_posts(keyword, num_posts=500, skip=False):
    # Supports keyword --> multiple subreddits
    subreddits = keyword_to_subreddits(keyword)
    for sr in subreddits:
        print("Checking if comments exist for {}".format(sr))
        if(not check_for_comments(sr)):
            
            print("For {}, comments in {}".format(
                sr, get_and_dump(sr, num_posts, keyword)))

    return subreddits


def main():
    """ Taking in subreddits, this script queries pushshift.io 
    to get submissions in the last year, gets associated comments,
    and saves compressed view of comment data."""
    subreddit_list = sys.argv[1], sys.argv[2], sys.argv[3]

    # TBA: Parallelize
    sr = sys.argv[1]

    get_and_dump(sr)


if __name__ == "__main__":
    main()
