import sys
sys.path.append("..")
from crowdrank import postprocessing
from crowdrank import helpers
from crowdrank import ingester


# Test 0...5: Unit tests



# Test: full postprocessing
def full_postprocess_test(keyword):
    try:
        use_s3 = helpers.bucket_exists()
    except:
        use_s3 = False
    df = postprocessing.postprocess(keyword, xref=True, lookback_days=360, use_s3=use_s3)
    print(df)

# Test: DataHandler object
def make_datahandler():
    # Use a random keyword, create datahandler object
    keyword = 'tablets'.capitalize()
    dh = ingester.DataHandler(keyword, num_posts=20, skip = False, use_s3 = helpers.in_S3())
    comment_bodys = dh.get_recent_posts()
    print(comment_bodys)

#data_handler = make_datahandler()

full_postprocess_test('tablets')
