import json
import spacy
import boto3



def get_prod_orgs(text, nlp):
    '''Get PRODs and ORGs based on the spaCy NER.'''
    prod_orgs = []
    doc = nlp(text)
    for ent in doc.ents:
        print(ent.text, ent.start_char, ent.end_char, ent.label, ent.label_)    
        if(ent.label ==383 or ent.label== 386):
            # If it's an ORG, and the next token is alphanumeric combo (SR800, S300, HD599, etc),
            # then add that to it?
            prod_orgs.append((ent.text, ent.label))
    return prod_orgs  

def get_data_S3(bucketname, keyname):
  s3 = boto3.resource('s3')
  content_obj = s3.Object(bucketname, keyname)
  json_content = json.loads(content_object.get()['Body'].read().decode())
  print(json_content['body'])



def get_entities_ndjson(pathname, nlp):

  print('start')
  c = 0

  #'../data/reddit_subreddits.ndjson'
  entity_list = []
  with open('../data/RC_2019-11') as f:
    # For each line, aka each comment:
    for l in f:
      obj = json.loads(l)
      c += 1
      entity_list.extend(get_prod_orgs(obj['body'], nlp))

      if c >100:
        break
  
  return entity_list

  print('end')

def main():
  nlp = spacy.load("en_core_web_md")
  nlp.add_pipe(nlp.create_pipe('sentencizer'))

  entity_list = get_entities_ndjson("hi", nlp)
  print(entity_list)

main()