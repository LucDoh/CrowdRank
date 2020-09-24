import sys
import json
from fuzzywuzzy import fuzz
from collections import Counter


def post_process_results(results):
    '''Takes in the results list, and outputs a ranking of the entities'''
    results = remove_improbable_entities(results)
    processed_results = combine_like_entities(results)
    print(processed_results)

    result_dict = {}
    for r in processed_results:
        result_dict[r[0]] = r[1]
    
    return Counter(result_dict)

def remove_improbable_entities(results, cutoff = 3):
    '''Here we simply remove entities we consider improbable
    to be products/brand-names which will contribute to falsey increasing
    the number of mentions.  E.g. if less than 3 characters (dm, eq, tx)'''
    # Could also remove links from amazon, which will give amazon credit for its products
    new_results = []
    for r in results:
        if len(r[0]) >= cutoff:
            new_results.append(r)
    
    return new_results



def combine_like_entities(results, n = 3):
    '''Combines mentions of like-entities using fuzzy matching.
    The initial set consists of entities which have been mentioned
    at least n times.'''
    last_considered_brand = 0
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
                print(r[0], r2[0])
                running_score += r2[1]
        
        sum_scores.append(running_score)
    
    print(results[:last_considered_brand])
    print([rl[1] for rl in results[:last_considered_brand]])
    print(sum_scores)

    combined_results = [(r[0], sum_scores[i]) for i, r in enumerate(results[:last_considered_brand])]
    return combined_results


def fuzzy_matching(list_of_strs):
    '''A function for testing fuzzy_matching. Note: there are faster
    ways to check string similarity, like python-Levenshtein (C)'''

    str_a = "hi"
    str_b = "hi there"
    str_c = "aasshiadsd"
    r = fuzz.ratio(str_a, str_b)
    r2 = fuzz.partial_ratio(str_a, str_b)
    r3 = fuzz.partial_ratio(str_b, str_c)
    r4 = fuzz.partial_ratio(str_a, str_c)
    print(r, r2, r3, r4)


            
    
def main():
    with open("results.txt", 'r') as f:
        results = json.loads(f.readlines()[0])
    print(len(results)) 
    results = list(results)
    # results are in the form [["sony", 12], ..., ["wip",1]]

    ranking = postprocess_results(results)\
    print(ranking)


if __name__=="__main__":
    main()
