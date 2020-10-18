import sys
sys.path.append("..")
from crowdrank import ingester
from crowdrank import interpreter
from crowdrank import helpers


# Test 0: instatiate a Knowledgebase, count
# mentions
def interpret_simple_test():
    comments = [
        ("Apple Airpods are the worst", 2),
        ("Bose are cheap but great", 5),
        ("I own 2 pairs of Sennheisers. They have amazing build quality!", 3),
    ]

    kb_test = interpreter.Knowledgebase(comments)
    prod_sentiments = kb_test.interpret()
    print("Simple count: ", prod_sentiments)

# Test 1: instantiate a Knowledgebase object
# do NER + Sentiment Analysis
def interpret_VADER_ntest():
    comments = [
        ("Apple Airpods are the worst", 2),
        ("Bose are cheap but great", 5),
        ("I own 2 pairs of Sennheisers. They have amazing build quality!", 3),
    ]
    print("Input comments:", comments)

    kb_test = interpreter.Knowledgebase(comments)

    prod_sentiments = kb_test.interpret_with_sentiment(context="narrow")
    print("Community_score:", prod_sentiments)
    assert len(prod_sentiments) == 3


# Test 2: Incorporating context into KB class
def interpret_any_context():
    comments = [
        ("Apple Airpods are the worst", 2),
        ("Bose are cheap but great", 5),
        ("I own 2 pairs of Sennheisers. They have amazing build quality!", 3),
    ]
    print("Input comments:", comments)

    kb_test = interpreter.Knowledgebase(comments)
    prod_sentiments_wide = kb_test.interpret_with_sentiment("wide")
    print("Wide: {}".format(prod_sentiments_wide))
    prod_sentiments_narrow = kb_test.interpret_with_sentiment("narrow")
    print("Narrow: {}".format(prod_sentiments_narrow))
    assert len(prod_sentiments_wide) == len(prod_sentiments_narrow)
    return prod_sentiments_wide


# Test 4: Test saving to S3
def test_saving_to_S3(test_data):
    if helpers.in_S3():
        interpreter.save_to_S3(test_data, 'TEST', 0)
    
    assert(True)

# Test 5: Full interpreter run
def full_interpreter_test():
    use_s3 = helpers.in_S3()
    subreddits = ['laptops']
    keyword = 'laptops'
    comments = interpreter.get_and_interpret(subreddits, keyword, 360, use_s3 = use_s3)
    print(len(comments))




interpret_VADER_ntest()
interpret_simple_test()


print("Both...")
prod_sentiments_test = interpret_any_context()

print("Save to bucket test")
test_saving_to_S3(prod_sentiments_test)

print("Full interpreter test")
full_interpreter_test()
