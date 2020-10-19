import json
import requests
import sys
import boto3
import botocore


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


def save_json_to_S3(data, bucket_name, file_name):
    # filename, bucket_name, data
    s3 = boto3.resource("s3")
    s3object = s3.Object(bucket_name, file_name)
    s3object.put(Body=(bytes(json.dumps(data).encode("UTF-8"))))


def check_for_data_S3(file_name, bucket_name="crowdsourced-data-reddit"):
    # This could be made more efficient by
    # reading that file and handling exception
    s3 = boto3.resource("s3")
    my_bucket = s3.Bucket(bucket_name)
    for o in my_bucket.objects.all():
        if file_name == o.key:
            return True

    return False


def bucket_exists():
    # Check that main bucket exists
    s3 = boto3.resource("s3")
    return s3.Bucket("crowdsourced-data-reddit") in s3.buckets.all()


def in_S3():
    # Checks whether in S3, to control save/loads
    try:
        bucket_exists()
        return True
    except:
        return False


def count_comments(sr, lookback_days, use_s3=False):
    # Get number comments stored in 2D list
    comment_path = "comment_data/{}_{}.json".format(sr, lookback_days)
    if use_s3:
        s3 = boto3.resource("s3")
        content_object = s3.Object("crowdsourced-data-reddit", comment_path)
        comments_2D = json.loads(content_object.get()["Body"].read().decode("utf-8"))
    else:
        with open("../data/" + comment_path) as f:
            comments_2D = json.load(f)
    return sum([len(comments) for comments in comments_2D])


# Helper functions
def unpack_comments(comments_2D):
    # Unpack List[List[JSON]] of comments, keep body and score:
    comments_upvotes = []
    for i in range(len(comments_2D)):
        for comment in comments_2D[i]:
            try:
                comments_upvotes.append((comment["body"], comment["score"]))
            except KeyError:
                comments_upvotes.append((comment["body"], 1))
    return comments_upvotes

