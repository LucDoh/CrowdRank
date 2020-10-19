import json
import requests
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter
import sys
import boto3

from . import helpers


class Knowledgebase:
    """Class for interpreting Reddit comments/posts, from (comment_text, upvotes)
    tuples. Other features to be included: datetime """
    def __init__(self, comments):
        # comments = [(text_0, upvotes_0),...]
        self.comments = comments
        self.prod_sentiments = []
        self.context = "wide"
        self.nlp = self.initialize_spacy()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    def initialize_spacy(self):
        nlp = spacy.load("en_core_web_md")
        nlp.add_pipe(nlp.create_pipe("sentencizer"))
        return nlp

    def interpret(self):
        products = []
        for c in self.comments:
            products.extend(interpret_text(c[0], self.nlp))

        self.prod_mentions = Counter([p.lower() for p in products]).most_common()
        return self.prod_mentions

    def interpret_with_sentiment(self, context="narrow"):
        """ Uses NER and Vader to create seeds for community 
        scores. """
        product_sentiments = []
        for c in self.comments:
            if c[1] >= 0:
                product_sentiments.extend(
                    interpret_paragraph_context(c, self.nlp, context)
                )

        self.prod_sentiments = product_sentiments
        return self.prod_sentiments



def analyze_sentence_sentiment(sentence):
    """ Analyzes a sentence using VADER and returns the 
    compound score. Typical thresholds are:
    1) positive: compound score >= 0.05
    2) negative: compound score <= -0.05
    3) neutral: otherwise."""
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(sentence)
    compound_score = sentiment["compound"]
    return compound_score


def interpret_paragraph_context(comment, nlp, context):
    """ Transform paragraph comments into  entity-scores,
    (product, sentiment, agreement)"""
    if context == "narrow":
        return interpret_paragraph_narrow(comment, nlp)
    else:
        return interpret_paragraph_wide(comment, nlp)


def interpret_paragraph_narrow(comment, nlp):
    """ Splits text into sentences. For each sentence:
    i) Extracts product/org names using spaCy NER,
    ii) Uses VADER to get the sentiment. Returns a list
    of product/orgs with the compound score attached."""
    prods_sentiments = []
    doc = nlp(comment[0])
    sentences = [sent.string.strip() for sent in doc.sents]

    for s in sentences:
        doc = nlp(s)
        sentiment_score = analyze_sentence_sentiment(s)
        for ent in doc.ents:
            if ent.label == 383 or ent.label == 386 or ent.text.lower() == 'apple':
                prods_sentiments.append((ent.text.lower(), sentiment_score, comment[1]))

    return prods_sentiments


def interpret_paragraph_wide(comment, nlp):
    """ Identical to interpret_paragraph_narrow () with
    difference, sentiment is inferred from the entire
    post. This is important when people's sentiment
    is not contained in the sentence where they first
    mention a product. (Often) """
    prods_sentiments = []
    doc = nlp(comment[0])
    sentiment_score = analyze_sentence_sentiment(comment[0])
    for ent in doc.ents:
        if ent.label == 383 or ent.label == 386 or ent.text.lower() == 'apple':
            prods_sentiments.append((ent.text.lower(), sentiment_score, comment[1]))

    return prods_sentiments


def interpret_text(text, nlp):
    """ This extracts product/org names using spaCy NER."""
    doc = nlp(text)
    prod_orgs = []
    for ent in doc.ents:
        if ent.label == 383 or ent.label == 386:
            # Product extraction: If ORG + next token is alphanumeric (SR800, HD599)
            prod_orgs.append(ent.text)

    return prod_orgs


def get_comments_local(sr, lookback_days = 360):
    # Get comments
    comments_path = "../data/comment_data/{}_{}.json".format(sr, lookback_days)
    # List of lists of JSON objects (which are comment objects)
    with open(comments_path) as f:
        comments_2D = json.load(f)

    return helpers.unpack_comments(comments_2D)

def get_comments_S3(sr, lookback_days = 360):
    # Get comments
    key = "comment_data/{}_{}.json".format(sr, lookback_days)
    s3 = boto3.resource('s3')
    content_object = s3.Object('crowdsourced-data-reddit', key)
    comments_2D = json.loads(content_object.get()['Body'].read().decode('utf-8'))
    #s3.Bucket('crowdsourced-data-reddit')
    return helpers.unpack_comments(comments_2D)

def save_to_S3(prod_sentiments, keyword, lookback_days):
    # filepath + bucket_name + prod_sentiments
    s3 = boto3.resource('s3')
    file_name = "{}/{}_{}.json".format(
        "interpreted_data", keyword, lookback_days)
    s3object = s3.Object("crowdsourced-data-reddit", file_name)
    s3object.put(
        Body=(bytes(json.dumps(prod_sentiments).encode('UTF-8')))
    ) 
    return

# Main-like function, called in current pipeline
def get_and_interpret(subreddits, keyword, lookback_days=360, use_s3 = False):
    """ Interpret community sentiments (scores) from a set of subreddits"""
    # 1) Load comments and comment scores
    comments_upvotes = []
    for sr in subreddits:
        if use_s3:
            comments_upvotes.extend(get_comments_S3(sr, lookback_days))
        else:
            comments_upvotes.extend(get_comments_local(sr, lookback_days))

    # 2) Build knowledgebase from list of comments
    kb = Knowledgebase(comments_upvotes)
    print("Subreddits: {}".format(subreddits))
    print("Comments analyzed: {}".format(len(kb.comments)))

    # 3) Extract product names and sentiments towards them
    prod_sentiments = kb.interpret_with_sentiment(context="wide")
    print("Number of entities found: {}".format(len(prod_sentiments)))

    # 4) Save results, in the form [(e_00, s_00, a_00), ... (e_Nm, s_Nm, a_Nm)]
    if not use_s3:
        file_out = "../data/interpreted_data/{}_{}.json".format(keyword, lookback_days)
        with open(file_out, "w") as f:
            json.dump(prod_sentiments, f)
    else:
        save_to_S3(prod_sentiments, keyword, lookback_days)

    return comments_upvotes #prod_sentiments
