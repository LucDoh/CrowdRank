import sys
import json
import pandas as pd
from fuzzywuzzy import fuzz
from collections import Counter



def combine_scorevectors(vec_1, vec_2):
    # score_1 = (e_1, s_1, a_1), score_2 = (e_2, s_2, a_2)
    
    # If vec_1 and vec_2 correspond to the same entity, i.e.
    # if(score_1[0] == score_2[0])
    
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


def fuzzy_matching(list_of_strs):
    '''Test function for fuzzy_matching. A faster way to 
    compute string similarity is likely python-Levenshtein (C)'''

    str_a, str_b, str_c = "hi", "hi there", "aasshiadsd"
    r = fuzz.ratio(str_a, str_b)
    r2 = fuzz.partial_ratio(str_a, str_b)
    r3 = fuzz.partial_ratio(str_b, str_c)
    r4 = fuzz.partial_ratio(str_a, str_c)
    print(r, r2, r3, r4)


def postprocess_results(results, known_brands):
    '''Takes in list of (product, # of occurences)
    Outputs'''
    results = remove_improbable_entities(results)
    processed_results = combine_like_entities(results)
    print(processed_results)

    result_dict = {}
    for r in processed_results:
        if r[0] in set(known_brands):
            result_dict[r[0]] = r[1]
    
    return Counter(result_dict)


def postprocess_sentimentful_results(results, known_brands):
    '''Takes in list of (product, sentiment, agreement),
    then performs similar operations as postprocess.'''
    results_filepath = "../data/interpreted_data/{}_{}.json".format(subreddit, lookback_days)
    with open(results_filepath, 'r') as f:
        results = json.loads(f.readlines()[0])
    load_results(subreddit, lookback_days)
    #results = remove_improbable_entities(results)

    #processed_results = combine_like_entities(results)
    return


def postprocess(subreddit, lookback_days = 360):
    '''Postprocessing includes: fuzzy string matching,
    removing 1 and 2 letter entities, and uses a list of
    brands to make the final ranking.'''

    results_filepath = "../data/interpreted_data/{}_{}.json".format(subreddit, lookback_days)
    with open(results_filepath, 'r') as f:
        results = json.loads(f.readlines()[0])

    print("Number of entities: {}".format(len(results)))
    results = list(results)
    # results are in the form [["sony", 12], ..., ["wip",1]]

    known_brands = [] 
    with open("../data/product_data/brands.txt", 'r') as f:
        known_brands = [line[:-1] for line in f]
    
    ranking = postprocess_results(results, known_brands)
    df = pd.DataFrame(ranking)
    df.columns = ["Brand", "Mentions"]

    print(ranking)

    out_path = "../data/results/{}_{}.csv"
    df.to_csv(out_path, index=False)
        
    return df


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


