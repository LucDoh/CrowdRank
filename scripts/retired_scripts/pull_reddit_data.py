import json
import requests
import spacy
import nltk
from collections import Counter
import sys


#####################
# Given user-input subreddits, this script grabs all
# submissions in them that are deemed to be "recommendation/advice"
# posts, then grabs all the comments associated with them.
# This data is 
# This needs to be refactored


### Should add a class here which describes our search
# and from which methods are run?
### Attributes: kw_1, kw_2, subreddit_1, subreddit_2, time_range





############# START (Unused) #################

def get_ents(text):
    '''Returns all entities, and their labels.'''
    entities = []
    doc = nlp(text)
    for ent in doc.ents:
        #print(ent.text, ent.start_char, ent.end_char, ent.label, ent.label_)
        entities.append((ent.text, ent.label_))
    
    return entities

        
def get_ents_sentsplit(text):
    '''Similar to below, but split by sentences.'''
    doc = nlp(text)
    sentences = [sent.string.strip() for sent in doc.sents]
    
    for s in sentences:
            doc = nlp(s)
            for ent in doc.ents:
                print(ent.text, ent.start_char, ent.end_char, ent.label_)
                print([(token.idx, token, type(token), token.nbor()) for token in ent])
                
def candidate_products(text):
    '''This should return surrounding words, and do some processing for a better attempt at
    product recognition.'''
    doc = nlp(text)
    product_list = []
    likely_product = []
    sentences = [sent.string.strip() for sent in doc.sents]
    
    for s in sentences:
            doc = nlp(s)
            for ent in doc.ents:
                #print(ent.text, ent.start_char, ent.end_char, ent.label_)
                #print([(token.idx, token, type(token), token.nbor()) for token in ent])
                #print([(token, token.nbor()) for token in ent])
                for token in ent:
                    try:
                        product_list.extend([(token, token.nbor())])
                    except:
                        print("IndexError")
                        
                if(ent.label == 380): #Product
                    likely_product.append(ent.text)
    return product_list, likely_product


def multisubreddit_products():
    # Let's grab data from 3 subreddits about headphones:
    # Headphoneadvice, audiophile, BudgetAudiophile
    subreddits = ['headphoneadvice', 'budgetaudiophile', 'audiophile']
    prod_list_from_srs = []
    for sr in subreddits:
        h_page = requests.get('http://api.pushshift.io/reddit/search/submission/?subreddit={}&q=best+recommend&before=360d'.format(sr))
        h_data = json.loads(h_page.text)
        agg_prod_list = get_cmted_prods_submissions(h_data)
        
        prod_list_from_srs.extend(agg_prod_list)
    
    # Now, let's count and rank products (this is the result data)
    return Counter([p.lower() for p in prod_list_from_srs]).most_common()


############# END #################


def get_prod_orgs(text, nlp):
    '''Get PRODs and ORGs based on the spaCy NER.'''
    prod_orgs = []
    doc = nlp(text)
    for ent in doc.ents:
        #print(ent.text, ent.start_char, ent.end_char, ent.label, ent.label_)    
        if(ent.label ==383 or ent.label== 386):
            # TBA : If an ORG, and the next token is alphanumeric combo (SR800, HD599) then add product
            prod_orgs.append(ent.text)
    return prod_orgs  


def get_assoc_comments(d):
    ''' Using a submission JSON, return a new JSON of all comments.'''
    c_page = requests.get('https://api.pushshift.io/reddit/submission/comment_ids/{}'.format(d['id']))
    c_data = json.loads(c_page.text)
    
    cs_page = requests.get('https://api.pushshift.io/reddit/comment/search?ids={}'.format(",".join(c_data['data'])))
    cs_data = json.loads(cs_page.text)
    
    return(cs_data['data'])



def get_cmted_prods_submissions(submissions_data, nlp):
    '''This takes in the JSON data returned from a query to a specific subreddit, 
    gets all associated comments and then returns an aggregate "product-list" from
    all this comment data.'''
    agg_product_list = []
    total_comments = 0
    total_submissions = 0
    for h_d in submissions_data['data']:
        comments = get_assoc_comments(h_d) #d
        total_submissions += 1
        total_comments += len(comments)
        
        for c in comments:
            agg_product_list.extend(get_prod_orgs(c['body'], nlp))
            
    print("Comments = {}".format(total_comments))
    print("Submissions scanned = {}".format(total_submissions))
    
    return agg_product_list

def get_many_submissions(subreddit_list, lookback_days = 360):
    '''Iterates through subreddits, pulls submissions for the last n days. Then gets
    all associated comments, and extracts product names from it. '''

    prod_list_from_srs = []

    nlp = spacy.load("en_core_web_md")
    nlp.add_pipe(nlp.create_pipe('sentencizer'))

    for sr in subreddit_list:
        print("Looking at {}".format(sr))
        h_page = requests.get('http://api.pushshift.io/reddit/search/submission/?subreddit={}&q=best+advice+recommendations&before={}d&size=500'.format(sr,lookback_days))
        # Put all this data on S3
        #print(h_page.text)
        h_data = json.loads(h_page.text)
        agg_prod_list = get_cmted_prods_submissions(h_data, nlp)
        # Get associated comments, paste this in S3

        prod_list_from_srs.extend(agg_prod_list)
    
    return Counter([p.lower() for p in prod_list_from_srs]).most_common()

#########
# Add functions which will pull data, eventually pushing to S3

def get_comments_save(subreddit_list, file_out="results.txt"):
    results = get_many_submissions(subreddit_list)
    with open(file_out,'w') as f:
        f.write(json.dumps(results))



def main():
    subreddit_list = sys.argv[1], sys.argv[2], sys.argv[3]
    # TBA: Parallelize
    get_comments_save(subreddit_list)

if __name__=="__main__":
    main()




