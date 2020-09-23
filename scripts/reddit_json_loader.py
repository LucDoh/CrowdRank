import json

with open('RC_2019-11_10.zst') as infile:
  o = json.load(infile)

print(o)
