import sys
import json
import requests
import numpy as np
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter
import boto3

from . import helpers


class Knowledgebase:
    """Class for interpreting Reddit comments/posts, from (comment_text, upvotes)
    tuples. Other features to be included: datetime """

    def __init__(self, comments, context = 'wide'):
        # comments = [(text_0, upvotes_0),...]
        self.comments = comments
        self.prod_sentiments = []
        self.context = context
        self.nlp = self.initialize_spacy()
        self.comment_analyzer = CommentAnalyzer(self.context, self.nlp)

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
                    self.comment_analyzer.interpret_paragraph_context(c)
                )
                
        self.prod_sentiments = product_sentiments
        return self.prod_sentiments


class CommentAnalyzer:
    ''' Interpret comment-by-comment. An instance of this
    object has a context variable, SpaCy's general-purpose
    nlp object and VADER's SentimentIntensityAnalyzer as its
    attributes. '''
    def __init__(self, context, nlp):
        self.context = context
        self.nlp = nlp
        self.sentiment_analyzer = SentimentIntensityAnalyzer()


    def analyze_sentence_sentiment(self, sentence):
        """ Analyze a sentence using VADER and return the 
        compound score. Typical thresholds are:
        1) positive: compound score >= 0.05
        2) negative: compound score <= -0.05
        3) neutral: otherwise."""
        sentiment = self.sentiment_analyzer.polarity_scores(sentence)
        compound_score = sentiment["compound"]
        return compound_score


    def interpret_paragraph_context(self, comment):
        """ Transform paragraph comments into  entity-scores,
        (product, sentiment, agreement)"""
        if self.context == "narrow":
            return self.interpret_paragraph_narrow(comment)
        else:
            return self.interpret_paragraph_wide(comment)


    def interpret_paragraph_narrow(self, comment):
        """ Splits text into sentences. For each sentence:
        i) Extracts product/org names using spaCy NER
        ii) Uses VADER to analyze sentiment. Returns a list
        of tuples of (product, compund_score, upvotes). """ 
        prods_sentiments = []
        doc = self.nlp(comment[0])
        sentences = [sent.string.strip() for sent in doc.sents]

        for s in sentences:
            doc = self.nlp(s)
            sentiment_score = self.analyze_sentence_sentiment(s)
            for ent in doc.ents:
                if ent.label == 383 or ent.label == 386: 
                    prods_sentiments.append((ent.text.lower(), sentiment_score, comment[1]))

        return prods_sentiments


    def interpret_paragraph_wide(self, comment):
        """ Identical to interpret_paragraph_narrow() with
        a key difference: sentiment is inferred from the whole
        post. This is important when sentiment is not contained
        in the sentence where they explicitly mention a product. """
        prods_sentiments = []
        doc = self.nlp(comment[0])
        sentences = [sent.string.strip() for sent in doc.sents]
        scores = [self.analyze_sentence_sentiment(s) for s in sentences]
        sentiment_score = np.average(scores)
        for ent in doc.ents:
            if ent.label == 383 or ent.label == 386: 
                prods_sentiments.append((ent.text.lower(), sentiment_score, comment[1]))

        return prods_sentiments


    def interpret_text(self, text):
        """ This extracts product/org names using spaCy NER."""
        doc = self.nlp(text)
        prod_orgs = []
        for ent in doc.ents:
            if ent.label == 383 or ent.label == 386:
                # Product extraction: If ORG + next token is alphanumeric (SR800, HD599)
                prod_orgs.append(ent.text)

        return prod_orgs



def get_comments_local(sr, lookback_days=360):
    # Get comments
    comments_path = "../data/comment_data/{}_{}.json".format(sr, lookback_days)
    # List of lists of JSON objects (which contain all comment data)
    with open(comments_path) as f:
        comments_2D = json.load(f)

    return helpers.unpack_comments(comments_2D)


def get_comments_S3(sr, lookback_days=360):
    # Get comments
    key = "comment_data/{}_{}.json".format(sr, lookback_days)
    s3 = boto3.resource("s3")
    content_object = s3.Object("crowdsourced-data-reddit", key)
    comments_2D = json.loads(content_object.get()["Body"].read().decode("utf-8"))
    return helpers.unpack_comments(comments_2D)


def save_to_S3(prod_sentiments, keyword, lookback_days):
    # Save all obtained prod_sentiments for the keyword to S3
    s3 = boto3.resource("s3")
    file_name = "{}/{}_{}.json".format("interpreted_data", keyword, lookback_days)
    s3object = s3.Object("crowdsourced-data-reddit", file_name)
    s3object.put(Body=(bytes(json.dumps(prod_sentiments).encode("UTF-8"))))



def get_and_interpret(subreddits, keyword, lookback_days=360, use_s3=False):
    """ Interpret community sentiments (scores) from a set of subreddits. 
    This is a main-like function, called in the pipeline to grab comments
    and then create a Knowledgebase object for comment analysis. """

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

    return comments_upvotes
