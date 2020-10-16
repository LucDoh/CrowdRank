<p align="center">
<img width="55%" src='static/CrowdRank_Logo.png'>
</p>

## Description
CrowdRank is an end-to-end package for interpreting community sentiments about brands and products from Reddit data. From a single keyword describing a product category (headphones, computers, laptops, tvs), skim through and interpret thousands of relevant comments and get back a ranking of the best brands in that space.


NLP Models: SpaCy [Named Entity Recognition], VADER [Sentiment Analysis].  
Tech Stack: Python, AWS EC2, JSON.  
Some packages: Requests, Pandas, Fuzzywuzzy, Streamlit...

## Data
Over 4 billion Reddit posts, queryable through [Pushshift's API](https://reddit-api.readthedocs.io/en/latest/).

## Motivation
210 million Americans shop online every year and 80% of them do research before purchasing an item. There 1000s of products in the same category (e.g. Wireless Headphones) with over 4 stars, making it almost impossible to sort through them. What if we could tap into the collective knowledge of communities, to help users quickly choose the best brands and products?

This web app and package tackle that problem, by using NLP to quickly and intelligently turn thousands of comments into a simple ranking of brands with 2 scores: "Community Score" and "Popularity".

## Results (web app)
...  
## Results (package)
...  
## Usage
Then, run the web app from inside scripts/:  
streamlit run crowdrank_app.py

## Installing
Clone the repository:  
git clone https://github.com/LucDoh/CrowdRank.git  

Make subdirectories inside data/:  
mkdir comment_data interpreted_data submission_data results

Install requirements:  
pip install -r requirements.txt  
python -m spacy download en_core_web_md




