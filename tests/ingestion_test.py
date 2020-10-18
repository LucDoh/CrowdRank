import sys
sys.path.append("..")

from crowdrank import ingester
from crowdrank import interpreter
from crowdrank import helpers


## Test 1: do a full ingestion with 3 CL arguments
def test_ingestion_pipeline():
    keyword = sys.argv[1]
    subreddit = sys.argv[2]
    num_posts = 1 if len(sys.argv) == 3 else sys.argv[3]
    comments = ingester.get_and_dump(subreddit, num_posts, keyword, 360)[0]
    assert comments
    return comments


# Test 2: Get comments associated with a submission id
# Example id: 'jcgmcd' --> r/laptops/comments/jcgmcd/is_the_apple_macbook_pro_worth_it/
def test_get_comments():
    comments = ingester.get_assoc_comments('jcgmcd')
    unpacked_comments = []
    for c in comments:
        unpacked_comments.extend(c)
    assert unpacked_comments
    return len(unpacked_comments)

# Test 3: Check for bucket existence
def test_is_ec2():
    try:
        assert(ingester.bucket_exists())
        print("Bucket exists (and on EC2)")
        return True
    except:
        print("Running locally or bucket DNE")
        return False

# Test 4: Testing whole module on small dataset
def full_ingestion_S3(use_S3):
    keyword = sys.argv[1]
    subreddit = sys.argv[2]
    num_posts = 1 if len(sys.argv) == 3 else sys.argv[3]
    dh = ingester.DataHandler(keyword, num_posts=num_posts, skip = False, use_s3 = helpers.in_S3())
    comment_bodys = dh.get_recent_posts()
    print(comment_bodys)
    assert True


print(test_ingestion_pipeline())
print(test_get_comments())

# Test full ingestion, based on system
full_ingestion_S3(test_is_ec2())
