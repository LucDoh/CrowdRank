import sys
import json
import pandas as pd
from fuzzywuzzy import fuzz
from collections import Counter
from emoji import UNICODE_EMOJI

def is_emoji(s):
    return s in UNICODE_EMOJI


# Need to add a class to make processing step more clear.


def combine_scorevectors(vec_1, vec_2):
    '''Combining two entity-score vectors,
    e.g. vec_1 = (e_1, s_1, a_1), vec_2 = (e_2, s_2, a_2)'''
    total_agreements = vec_1[2] + vec_2[2]
    normed_sentiment = (vec_1[1]*vec_1[2] + vec_2[1]*vec_2[2])/total_agreements

    combined_vector = (vec_1[0], normed_sentiment, total_agreements)
    return combined_vector


def remove_improbable_entities(results, cutoff = 3):
    '''Here we simply remove entities we consider improbable
    to be products/brand-names which will contribute to falsey increasing
    the number of mentions.  E.g. if less than 3 characters (dm, eq, tx)'''
    # Should remove links from Amazon, which give amazon undue credit.
    new_results = []
    for r in results:
        if len(r[0]) >= cutoff:
            new_results.append(r)
    
    return new_results


def combine_like_entities(results, n = 3):
    '''Combines mentions of like-entities using fuzzy matching.
    The initial set consists of entities which have been mentioned
    at least n times.'''

    for i, tupe in enumerate(results):
        if tupe[1] < n:
            last_considered_brand = i
            break
        
    sum_scores = []
    for i, r in enumerate(results[:last_considered_brand]):
        running_score = 0
        running_score += r[1]
        for r2 in results[last_considered_brand:]:
            if fuzz.partial_ratio(r[0], r2[0]) >= 95:
                running_score += r2[1]
        
        sum_scores.append(running_score)
    
    print(results[:last_considered_brand])
    print([rl[1] for rl in results[:last_considered_brand]])
    print(sum_scores)

    combined_results = [(r[0], sum_scores[i]) for i, r in enumerate(results[:last_considered_brand])]
    return combined_results

def aggregate_score(tuples):
    # Tuples are a list of [(sentiment_0, agreement_0),...]
    print(tuples)
    unscaled_sentiment = 0
    total_votes = 0
    if not tuples:
        return (0, 0, 0)
    for tuple in tuples:
        total_votes += tuple[1]
        unscaled_sentiment += tuple[0]*tuple[1]
    mean_score = unscaled_sentiment/total_votes

    # Get variance (two-pass method)
    variance_numerator = 0
    for tuple in tuples:
        variance_numerator += tuple[1]*((mean_score - unscaled_sentiment)**2)
    score_variance = variance_numerator/total_votes
    
    return (mean_score, total_votes, score_variance)

def apply_aggregate_scoring(entity_score_dict):
    scored_entities = {}
    for key, val in entity_score_dict.items():
        scored_entities[key] = aggregate_score(val)

    return scored_entities

def check_match(entity_1, entity_2, threshold = 95):
    return fuzz.partial_ratio(entity_1, entity_2) >= threshold

def combine_sentimentful_entities(results, top_entities):
    '''Combines mentions of like-entities using fuzzy matching,
    and adds together their scores via weighted averages. Also
    gives variance...'''

    # Construct a dictionary so that we can keep track of 
    # all these scores and do thorough scoring after
    entity_score_dict = {}

    for entity in top_entities:
        entity_score_dict[entity] = []
        for r in results:
            # If they match, add sentiment-agreement tuple to list
            if(check_match(entity, r[0])):
                entity_score_dict[entity].append((r[1], r[2]))

    # In theory, after all this we should have a dict whose keys
    # are entity strings and whose values are lists of sentiment-agreement 
    # tuples. e.g. entity_score_dict['sony'] = [(0.05, 10), (0.1, 2), (-0.4, 3)]

    # Now, let's define a function which will collapse the values of these dicts
    # into a tuple: (mean_sentiment, total_agreements, sentiment_variance)
    
    scored_entities = apply_aggregate_scoring(entity_score_dict)



    return scored_entities


def fuzzy_matching(list_of_strs):
    '''Test function for fuzzy_matching. A faster way to 
    compute string similarity is likely python-Levenshtein (C)'''

    str_a, str_b, str_c = "hi", "hi there", "aasshiadsd"
    r = fuzz.ratio(str_a, str_b)
    r2 = fuzz.partial_ratio(str_a, str_b)
    r3 = fuzz.partial_ratio(str_b, str_c)
    r4 = fuzz.partial_ratio(str_a, str_c)
    print(r, r2, r3, r4)

def confirm_known_brands(results, known_brands):
    result_dict = {}
    for r in results:
        if r[0] in set(known_brands):
            result_dict[r[0]] = r[1]
    return result_dict

def postprocess_results(results, known_brands):
    '''Takes in list of (product, # of occurences)
    Outputs popularity ranking... This is the original
    version of postprocess_sentimentful_results.'''
    results = remove_improbable_entities(results)
    processed_results = combine_like_entities(results)
    print(processed_results)

    result_dict = confirm_known_brands(processed_results, known_brands)
    
    return Counter(result_dict)

def get_top_entities(results, fraction = 0.2):
    entities = [r[0].lower() for r in results]
    entity_counter = Counter(entities).most_common()
    # Get top 20% as seed brands
    top_entities = [e[0] for e in entity_counter[:len(entity_counter)//int(1/fraction)]]
    return top_entities


def postprocess_sentimentful_results(results, xref, known_brands):
    '''Takes in list of (product, sentiment, agreement),
    then performs similar operations as postprocess.'''
    
    # Should have at least 3 characters to be a brand. 
    results = remove_improbable_entities(results, cutoff = 3)
    top_entities = get_top_entities(results)
    scored_entities = combine_sentimentful_entities(results, top_entities)

    # Combine entities which have extreme string similarity (sennheiser, sennheizer sr500)
    #processed_results = combine_like_entities(results)
    
    #Finally, check if these keys correspond to known_brands
    if xref:
        scored_entities = {key: scored_entities[key] for key in scored_entities.keys() if key in known_brands}

    return scored_entities #scored_entities


def postprocess(subreddit, xref = True, lookback_days = 360):
    '''Postprocessing includes: fuzzy string matching,
    removing 1 and 2 letter entities, and uses a list of
    brands to make the final ranking.'''

    results_filepath = "../data/interpreted_data/{}_{}.json".format(subreddit, lookback_days)
    with open(results_filepath, 'r') as f:
        results = json.loads(f.readlines()[0])

    print("Number of entities: {}".format(len(results)))
    results = list(results) # [["sony", 12], ..., ["wip",1]]

    known_brands = [] 
    with open("../data/product_data/brands.txt", 'r') as f:
        known_brands = [line[:-1] for line in f]
    
    ranking = postprocess_sentimentful_results(results, xref, known_brands)
    df = pd.DataFrame.from_dict(ranking, orient='index')
    df.columns = ['Sentiment', 'Popularity', 'Variance']
    df = df.sort_values(by=['Sentiment'], ascending=False)
    #df = pd.DataFrame(ranking)
    #df.columns = ["Brand", "Mentions"]

    #print(ranking)

    out_path = "../data/results/{}_{}.csv"
    df.to_csv(out_path)
        
    return df

def postprocess_multisubreddit(subreddits, xref = True, lookback_days = 360):
    ''' Support multiple subreddits...'''


    return #df



def main():

    results_filepath = str(sys.argv[1])
    with open(results_filepath, 'r') as f:
        results = json.loads(f.readlines()[0])
    print(len(results)) 
    results = list(results)
    

    known_brands = [] 
    with open("../data/product_data/brands.txt", 'r') as f:
        for line in f:
            known_brands.append(line[:-1])
    
    ranking = postprocess_results(results, known_brands)
    print(ranking)

    out_path = "/".join(results_filepath.split("/")[:-1]) + "ranking.txt"
    with open(out_path, 'w') as f:
        json.dump(ranking, f, indent  = 4)


if __name__=="__main__":
    main()


