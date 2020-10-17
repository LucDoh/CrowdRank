import sys
sys.path.append("..")

from crowdrank import ingester
from crowdrank import interpreter


## Test 1: do a full ingestion with 3 CL arguments
def test_ingestion_pipeline():
    keyword = sys.argv[1]
    subreddit = sys.argv[2]
    num_posts = 1 if len(sys.argv) == 3 else sys.argv[3]
    comments = ingester.get_and_dump(subreddit, num_posts, keyword, 360, dumppath="../data/")[0]
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
    # is_ec2() not working on EC2.
    # print("Running on EC2:", ingester.is_ec2())
    try:
        ingester.bucket_exists()
        print("Bucket exists")
    except:
        print("Bucket DNE or not an EC2 instance")

print(test_ingestion_pipeline())
print(test_get_comments())

test_is_ec2()
