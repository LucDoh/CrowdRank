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
    s3 = boto3.resource('s3')
    s3object = s3.Object(bucket_name, file_name)
    s3object.put(
        Body=(bytes(json.dumps(data).encode('UTF-8')))
    )

def check_for_data_S3(file_name, bucket_name = 'crowdsourced-data-reddit'):
    # This could be made more efficient by
    # reading that file and handling exception
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(bucket_name)
    for o in my_bucket.objects.all():
        if file_name == o.key:
            return True
    
    return False

def bucket_exists():
    # Check that main bucket exists
    s3 = boto3.resource('s3')
    return s3.Bucket('crowdsourced-data-reddit') in s3.buckets.all()

def in_S3():
    # Checks whether in S3, to control save/loads
    try:
        bucket_exists()
        return True
    except:
        return False

        


