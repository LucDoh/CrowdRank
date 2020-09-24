import json
import requests
import spacy
import nltk
from collections import Counter
import sys


#####################
#### Diff script


### Should add a class here which describes our search
# and from which methods are run?
### Attributes: kw_1, kw_2, subreddit_1, subreddit_2, time_range

def get_ents(text):
    '''Returns all entities, and their labels.'''
    entities = []
    doc = nlp(text)
    for ent in doc.ents:
        #print(ent.text, ent.start_char, ent.end_char, ent.label, ent.label_)
        entities.append((ent.text, ent.label_))
    
    return entities

        
def get_prod_orgs(text, nlp):
    '''Get PRODs and ORGs based on the spaCy NER.'''
    prod_orgs = []
    doc = nlp(text)
    for ent in doc.ents:
        print(ent.text, ent.start_char, ent.end_char, ent.label, ent.label_)    
        if(ent.label ==383 or ent.label== 386):
            # If it's an ORG, and the next token is alphanumeric combo (SR800, S300, HD599, etc),
            # then add that to it?
            prod_orgs.append(ent.text)
    return prod_orgs  
        
        
        
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

#########
# Add functions which will pull data, eventually pushing to S3

def get_comments_save(subreddit_list, file_out="results.txt"):
    results = get_submissions(subreddit_list)
    with open(file_out,'w') as f:
        f.write(json.dumps(results))
    

def get_submissions(subreddit_list):
    # Get a related submission and then all comments, e.g for advice/recommendations on headphones
    prod_list_from_srs = []
    # A) Get all posts in the subreddit headphones in the last year include the words best, advice, recommendations
    # Potentially parallelizable

    nlp = spacy.load("en_core_web_md")
    nlp.add_pipe(nlp.create_pipe('sentencizer'))

    for sr in subreddit_list:
        # This will only grab up to 100 posts, to get the rest need to:
        # Get the created_utc parameter from the last item in the results and send a new request using that as a before parameter.
        h_page = requests.get('http://api.pushshift.io/reddit/search/submission/?subreddit={}&q=best+advice+recommendations&before=360d'.format(sr))
        # Put all this data on S3

        h_data = json.loads(h_page.text)
        agg_prod_list = get_cmted_prods_submissions(h_data, nlp)
        # Get associated comments, paste this in S3

        prod_list_from_srs.extend(agg_prod_list)
    
    return Counter([p.lower() for p in prod_list_from_srs]).most_common()


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
    all_likely_products = []
    agg_product_list = []
    total_comments = 0
    for h_d in submissions_data['data']:
        comments = get_assoc_comments(h_d) #d
        total_comments += len(comments)
        for c in comments:
            agg_product_list.extend(get_prod_orgs(c['body'], nlp))
            
    print("Comments = {}".format(total_comments))
    
    return agg_product_list




def main():
    subreddit_list = sys.argv[1], sys.argv[2], sys.argv[3]
    get_comments_save(subreddit_list)

if __name__=="__main__":
    main()




