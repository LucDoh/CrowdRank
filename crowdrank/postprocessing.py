import sys
import json
import pandas as pd
from fuzzywuzzy import fuzz
from collections import Counter
from emoji import UNICODE_EMOJI


def is_emoji(s):
    return s in UNICODE_EMOJI

def combine_scorevectors(vec_1, vec_2):
    """Combining two entity-scores, e.g. 
    (e_1, s_1, a_1) and (e_2, s_2, a_2)"""
    total_agreements = vec_1[2] + vec_2[2]
    normed_sentiment = (vec_1[1] * vec_1[2] + vec_2[1] * vec_2[2]) / total_agreements
    return (vec_1[0], normed_sentiment, total_agreements)

def check_match(entity_1, entity_2, threshold=95):
    return fuzz.partial_ratio(entity_1, entity_2) >= threshold


def remove_improbable_entities(results, cutoff=3):
    """Remove improbable entities. E.g. if less than 3 characters (dm, eq, tx)"""
    # Should remove links from Amazon, which give amazon undue credit.
    new_results = []
    for r in results:
        if len(r[0]) >= cutoff:
            new_results.append(r)

    return new_results


def combine_like_entities(results, n=3):
    """Combine similar-entities using fuzzy matching, e.g. Bose & Bose WM500.
    Initial set: entities which have been mentioned at least n times."""

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

    combined_results = [
        (r[0], sum_scores[i]) for i, r in enumerate(results[:last_considered_brand])
    ]
    return combined_results


def aggregate_score(tuples):
    # Tuples are a list of [(sentiment_0, agreement_0),...]
    unscaled_sentiment = 0
    total_votes = 0
    if not tuples:
        return (0, 0, 0)
    for tuple in tuples:
        total_votes += tuple[1]
        unscaled_sentiment += tuple[0] * tuple[1]

    if total_votes == 0:
        total_votes = 1  # Keep their opinion if 1 downvote

    mean_score = unscaled_sentiment / total_votes

    # Get variance (two-pass method)
    variance_numerator = 0
    for tuple in tuples:
        variance_numerator += tuple[1] * ((mean_score - unscaled_sentiment) ** 2)
    score_variance = variance_numerator / total_votes

    return (mean_score, total_votes, score_variance)


def apply_aggregate_scoring(entity_score_dict):
    scored_entities = {}
    for key, val in entity_score_dict.items():
        scored_entities[key] = aggregate_score(val)

    return scored_entities


def combine_sentimentful_entities(results, top_entities):
    """Combines mentions of like-entities using fuzzy matching,
    and adds together their scores via weighted averages. Also
    gives variance..."""

    # Dictionary to track scores of top brands/products
    entity_score_dict = {}

    for entity in top_entities:
        entity_score_dict[entity] = []
        for r in results:
            # If they match, add sentiment-agreement tuple to list
            if check_match(entity, r[0]):
                entity_score_dict[entity].append((r[1], r[2]))

    # Aggregate scores from this dictionary, {entity_string : [community_score, popularity]}
    # e.g. entity_score_dict['sony'] = [(0.05, 10), (0.1, 2), (-0.4, 3)]
    scored_entities = apply_aggregate_scoring(entity_score_dict)

    return scored_entities


def fuzzy_matching(list_of_strs):
    """Test function for fuzzy_matching. A faster way to 
    compute string similarity is likely python-Levenshtein (C)"""

    str_a, str_c = "hi", "aasshiadsd"
    r = fuzz.ratio(str_a, str_c)
    r2 = fuzz.partial_ratio(str_a, str_c)
    print(r, r2)


def confirm_known_brands(results, known_brands):
    '''Crossreference with a list of known_brands'''
    result_dict = {}
    for r in results:
        if r[0] in set(known_brands):
            result_dict[r[0]] = r[1]
    return result_dict


def postprocess_results(results, known_brands):
    """ Deprecated: Takes in (product, # of occurences)
    and popularity ranking..."""
    results = remove_improbable_entities(results)
    processed_results = combine_like_entities(results)
    result_dict = confirm_known_brands(processed_results, known_brands)
    return Counter(result_dict)


def get_top_entities(results, fraction=0.2):
    entities = [r[0].lower() for r in results]
    entity_counter = Counter(entities).most_common()
    # Get top 20% as seed brands
    top_entities = [
        e[0] for e in entity_counter[: len(entity_counter) // int(1 / fraction)]
    ]
    return top_entities


def postprocess_sentimentful_results(results, xref, known_brands):
    """Takes in list of (product, sentiment, agreement),
    processes this into a ranking by score aggregation and
    fuzzy-matching."""

    results = remove_improbable_entities(results, cutoff=3)
    top_entities = get_top_entities(results)
    scored_entities = combine_sentimentful_entities(results, top_entities)

    # Cross-reference (keys correspond to known_brands)
    if xref:
        scored_entities = {
            key: scored_entities[key]
            for key in scored_entities.keys()
            if key in known_brands
        }

    return scored_entities 


def postprocess(
    keyword, xref=True, lookback_days=360
): 
    """Postprocessing includes: fuzzy string matching,
    removing 1 and 2 letter entities, and uses a list of
    brands to make the final ranking."""

    results_filepath = "../data/interpreted_data/{}_{}.json".format(
        keyword, lookback_days
    )
    with open(results_filepath, "r") as f:
        results = json.loads(f.readlines()[0])

    print("Number of entities: {}".format(len(results)))
    results = list(results)  # [["sony", 12], ..., ["wip",1]]

    brands_path = (
        "../data/product_data/headphones_brands.txt"
        if (keyword == "Headphones")
        else "../data/product_data/brands.txt"
    )
    print("Brands path: {}".format(brands_path))
    with open(brands_path, "r") as f:
        known_brands = [line[:-1] for line in f]

    ranking = postprocess_sentimentful_results(results, xref, known_brands)

    # Dataframe
    df = pd.DataFrame.from_dict(ranking, orient="index")
    df.columns = ["Sentiment", "Popularity", "Variance"]
    df = df.sort_values(by=["Sentiment"], ascending=False)
    df = df.round({"Sentiment": 2, "Variance": 2})


    out_path = "../data/results/{}_{}.csv".format(keyword, lookback_days)
    df.to_csv(out_path)

    return df