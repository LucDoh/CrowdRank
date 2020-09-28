import json
import requests
import spacy
from collections import Counter
import sys

class Knowledgebase():
    def __init__(self, comments):
        self.comments = comments
        self.prod_scores = []

    
    def interpret(self):
        nlp = spacy.load("en_core_web_md")
        nlp.add_pipe(nlp.create_pipe('sentencizer'))
        # For each comment, we're going to get all products mentioned
        products = []
        for c in self.comments:
            products.extend(interpret_text(c, nlp))

        # For now, score == mentions
        self.prod_scores = Counter([p.lower() for p in products]).most_common()
        return self.prod_scores


def interpret_text(text, nlp):
    ''' This extracts product/org names using spaCy NER.
    TBA: Sentiment analysis via VADER. First pass is
    i) Sentencize ii) Token gets sentiment of its sentence '''

    prod_orgs = []
    doc = nlp(text)

    for ent in doc.ents:
        #print(ent.text, ent.start_char, ent.end_char, ent.label, ent.label_)    
        if(ent.label == 383 or ent.label== 386):
            # TBA : If ORG, and next token is alphanumeric (SR800, HD599), then product
            prod_orgs.append(ent.text)

    return prod_orgs 


def get_local(sr, lookback_days = 360):
    # Get submissions?
    
    # Get comments
    comments_path = "../data/comment_data/{}_{}.json".format(sr, lookback_days)
    # List of lists of JSON objects (which are comment objects)
    with open(comments_path) as f:
        comments_2D = json.load(f)
    # Unpacking to just have a list of text
    comments = []
    for i in range(len(comments_2D)):
        for comment in comments_2D[i]:
            comments.append(comment['body'])

    return comments

def get_and_interpret(sr, lookback_days = 360):

    # 1) Load comments (only text, no metadata)
    comments = get_local(sr, lookback_days)

    # 2) Build knowledge object from list of comments
    kb = Knowledgebase(comments)
    print(len(kb.comments))

    #3) Extract product names, count for scores (and sentiment)
    prod_scores = kb.interpret()
    print(len(prod_scores))

    #4) Save results
    file_out = "../data/results/results_{}_{}.json".format(sr, lookback_days)
    with open(file_out,'w') as f:
        json.dump(prod_scores, f)

    return file_out


def main():
    subreddit_list = sys.argv[1] #, sys.argv[2], sys.argv[3]]
    # TBA: Parallelize
    sr = sys.argv[1]

    out_path = get_and_interpret(sr)

    print("Outputted to {}".format(out_path))

   


if __name__=="__main__":
    main()
