<div style='text-align:center'><img src='static/CrowdRank_Logo.png'></div>

## Description
CrowdRank is an end-to-end package for interpreting community sentiments about brands and products, from Reddit data. In the current implementation, it takes a category (headphones, computers, laptops, tvs) and skims through and interprets thousands of relevant comments to return a ranking of the best brands in that space.

NLP Models: SpaCy [Named Entity Recognition], VADER [Sentiment Analysis]

Tech Stack: Python, AWS EC2, Streamlit, JSON

## Motivation
210 million Americans shop online every year and 80% of them do research before purchasing an item. On Amazon, there 1000s of products in the same category (e.g. Wireless Headphones) with over 4 stars, making it almost impossible to sort through them. What if we could tap into the collective knowledge of communities, to help users quickly choose the best brands and products?

This web app and package aim to solve that problem, by using NLP to quickly and intelligently turn thousands of comments into a simple ranking with 2 scores: "Community Score" and "Popularity".

## Results (web app)

## Results (package)

## Usage
First, make subdirectories inside data/:  
mkdir comment_data interpreted_data submission_data results

Install requirements:  
pip install -r requirements.txt
python -m spacy download en_core_web_md

Then, simply the web app inside scripts/:  
streamlit run crowdrank_app.py


## Installing

