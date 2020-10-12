import json
import requests
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter
import sys

class Knowledgebase():
    '''Class for interpreting knowledge stored in 
    comments, constructed from a list of (comment_text, upvotes).'''
    def __init__(self, comments):
        # comments = [(text_0, upvotes_0),...]
        self.comments = comments
        self.prod_sentiments = []
    
    def interpret(self):
        nlp = spacy.load("en_core_web_md")
        nlp.add_pipe(nlp.create_pipe('sentencizer'))
        # For each comment, get products mentioned
        products = []
        for c in self.comments:
            products.extend(interpret_text(c[0], nlp))

        # For now, score == mentions
        self.prod_mentions = Counter([p.lower() for p in products]).most_common()
        return self.prod_mentions

    def interpret_with_sentiment(self, context = 'narrow'):
        '''Advanced version of interpret(), which
        uses a sentencizer and VADER to also get
        sentiment associated with brand mentions.'''
        nlp = spacy.load("en_core_web_md")
        nlp.add_pipe(nlp.create_pipe('sentencizer'))
        # For each comment, make a list of tuples (prod_i, sentiment_i)
        product_sentiments = []
        for c in self.comments:
             # (Entity_i, sentiment_i, agreement_i)
             if c[1] >= 0:
                if context == 'narrow':
                    product_sentiments.extend(interpret_paragraph(c, nlp))
                else:
                    product_sentiments.extend(interpret_paragraph_widecontext(c, nlp))

        # products_sentiments = [("Apple", 0.5, 1), ("Bose", -0.4, 9), ...]

        self.prod_sentiments = product_sentiments
        return self.prod_sentiments


    

def analyze_sentence_sentiment(sentence):
    ''' Analyzes a sentence using VADER and returns the 
    compound score. Typical thresholds are given by:
    1) positive: compound score >= 0.05
    2) negative: compound score <= -0.05
    3) neutral: otherwise.'''
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(sentence)
    compound_score = sentiment['compound']
    return compound_score


def interpret_paragraph(comment, nlp):
    ''' Splits text into sentences. For each sentence:
    i) Extracts product/org names using spaCy NER,
    ii) Uses VADER to get the sentiment. Returns a list
    of product/orgs with the compound score attached.'''
    prods_sentiments = []
    doc = nlp(comment[0])
    sentences = [sent.string.strip() for sent in doc.sents]
    
    for s in sentences:
            doc = nlp(s)
            sentiment_score = analyze_sentence_sentiment(s)
            for ent in doc.ents:
                if ent.label == 383 or ent.label == 386:
                    prods_sentiments.append((ent.text.lower(), sentiment_score, comment[1]))

    return prods_sentiments

def interpret_paragraph_widecontext(comment, nlp):
    ''' Identical to interpret_paragraph() with one
    key difference, sentiment is taken from the entire
    post. This is important when people's sentiment
    is not contained in the sentence where they mention
    a product. (Often) '''
    prods_sentiments = []
    doc = nlp(comment[0])
    sentiment_score = analyze_sentence_sentiment(comment[0])
    for ent in doc.ents:
        if ent.label == 383 or ent.label == 386:
                    prods_sentiments.append((ent.text.lower(), sentiment_score, comment[1]))
    
    return prods_sentiments

def interpret_text(text, nlp):
    ''' This extracts product/org names using spaCy NER.'''

    prod_orgs = []
    doc = nlp(text)

    for ent in doc.ents:
        #print(ent.text, ent.start_char, ent.end_char, ent.label, ent.label_)    
        if(ent.label == 383 or ent.label== 386):
            # Product extraction: If ORG, and next token is alphanumeric (SR800, HD599), then product
            prod_orgs.append(ent.text)

    return prod_orgs 


def get_local(sr, lookback_days = 360):
    # Get comments
    comments_path = "../data/comment_data/{}_{}.json".format(sr, lookback_days)
    # List of lists of JSON objects (which are comment objects)
    with open(comments_path) as f:
        comments_2D = json.load(f)
    # Unpacking into a list of (comment body, comment score)
    comments = []
    comments_upvotes = []

    # Turn comment JSONs into [(comment['body'], comment['score']),...]
    for i in range(len(comments_2D)):
        for comment in comments_2D[i]:
            comments.append(comment['body'])
            try:
                comments_upvotes.append((comment['body'], comment['score']))
            except KeyError:
                comments_upvotes.append((comment['body'], 1))

    return comments_upvotes

def get_and_interpret(subreddits, keyword, lookback_days = 360): 
    ''' Interpret community sentiments (scores) from a set of subreddits'''
    # 1) Load comments and comment scores
    comments_upvotes = []
    for sr in subreddits:
        comments_upvotes.extend(get_local(sr, lookback_days))

    # 2) Build knowledgebase from list of comments
    kb = Knowledgebase(comments_upvotes)
    print("Comments analyzed: {}".format(len(kb.comments)))

    #3) Extract product names and sentiments towards them
    prod_sentiments = kb.interpret_with_sentiment(context='wide')
    print("Number of entities found: {}".format(len(prod_sentiments)))
    
    #4) Save results, in the form [(e_00, s_00, a_00), ... (e_Nm, s_Nm, a_Nm)]
    file_out = "../data/interpreted_data/{}_{}.json".format(keyword, lookback_days)
    with open(file_out,'w') as f:
        json.dump(prod_sentiments, f)

    return prod_sentiments


def main():
    subreddit_list = sys.argv[1] #, sys.argv[2], sys.argv[3]]
    # TBA: Parallelize
    sr = sys.argv[1]

    out_path = get_and_interpret(sr)

    print("Outputted to {}".format(out_path))

   


if __name__=="__main__":
    main()
