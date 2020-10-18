import sys
sys.path.append("..")
from crowdrank import ingester
from crowdrank import interpreter


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

# Test 3: Interpret and save to S3
def save_interpretations_test():
    subreddits = ['laptops']
    keyword = 'laptops'
    comments = interpreter.get_and_interpret(subreddits, keyword, 360, use_s3 = True)
    print(len(comments))

interpret_VADER_ntest()
interpret_simple_test()


print("Both...")
interpret_any_context()

print("Save to bucket test")
save_interpretations_test()