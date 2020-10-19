<p align="center">
<img width="40%" src='static/CrowdRank_Logo.png'>
</p>
<p align="center">
<img src="https://img.shields.io/badge/python-3.6-blue.svg?style=flat" alt="made with python"> &nbsp;&nbsp;&nbsp;
<img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat" alt="made with python">&nbsp;&nbsp;&nbsp;
<img src="https://img.shields.io/badge/license-MIT-400080.svg?style=flat" alt="made with python"> 
</p>

## Description
CrowdRank is a package for interpreting community sentiments about brands and products from Reddit data. From a single keyword describing a product category (headphones, computers, laptops, tvs), CrowdRank will skim through and interpret thousands of relevant comments, aggregate the results, and give back a ranking of the best brands in the space.


Stack: Python, AWS (EC2 & S3), JSON.  
NLP Models: [SpaCy](https://github.com/explosion/spaCy) [Named Entity Recognition], [VADER](https://github.com/cjhutto/vaderSentiment) [Sentiment Analysis].    
Packages: Requests, Pandas, Fuzzywuzzy, Streamlit...  

## Data
Queried with [Pushshift's API](https://reddit-api.readthedocs.io/en/latest/) which indexes over 4 billion comments, dating back to 2007.  

For the web app, comment and post data is stored on S3, s.t. if data already exists, we just run interpret and process the results into
a ranking.   

## Motivation
210 million Americans shop online every year and 80% of them do research before purchasing an item. There 1000s of products in the same category (e.g. Wireless Headphones) with over 4 stars, making it almost impossible to sort through them. What if we could tap into the collective knowledge of communities, to help users quickly choose the best brands and products?

This web app and package tackle that problem, by using NLP to intelligently mine posts and get a simple ranking of brands by *Community Score* and *Popularity*. 

## Web app
Run the web app from inside scripts:  

    streamlit run crowdrank_app.py

Or simply use the app here:   

http://54.177.99.61:8501  

(Deployed using AWS on an EC2 instance with S3 storage)  

## Package
Run the package to see the best rankings of a product (e.g. laptops):

    python crowdrank_simple.py laptops

(inside scripts)

CrowdRank has 3 main modules: *ingester*, *interpreter*, *postprocessing*, which do the bulk of the work. Supporting functions are in the *helpers* and *visualizer* modules. The above script will soon be replaced by a single call to *ranker*:

    from crowdrank import ranker  
    df_ranking = ranker.rank('laptops')  

## Installing
Clone the repository:  

    git clone https://github.com/LucDoh/CrowdRank.git  

Make subdirectories inside data:  

    mkdir comment_data interpreted_data submission_data results

Install requirements:  

    pip install -r requirements.txt  
    python -m spacy download en_core_web_md
