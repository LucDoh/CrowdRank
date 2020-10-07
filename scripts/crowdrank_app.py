import sys
sys.path.append("..")
import os.path
import streamlit as st 
import pandas as pd
import seaborn as sns

from crowdrank import ingester
from crowdrank import interpreter
from crowdrank import postprocessing


def render_UI(df_ranking):
        df_ranking = df_ranking.iloc[:len(df_ranking)//2]
        ax = sns.barplot(x=df_ranking.index, y='Sentiment', data=df_ranking)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        st.pyplot()


if __name__=='__main__':

    st.title("CrowdRank")
    st.set_option('deprecation.showPyplotGlobalUse', False)
    
    keyword = st.sidebar.selectbox("What type of product are you looking for?", 
    ('', 'Headphones', 'Laptops', 'Computers', 'Keyboards', 'Mouses', 'Monitors', 'Tvs', 'Tablets', 'Smartwatches'))

    xref_response = st.sidebar.selectbox('Cross-reference brands?', ('Yes', 'No'))
    xref = (xref_response == 'Yes')
    if keyword != "":
        
        data_load_state = st.text("Loading Reddit data...")
        # If data exists, skip ingestion and interpreting
        if not os.path.exists('../data/results/{}_360.csv'.format(keyword)):
            num_posts = 500

            subreddits = ingester.get_recent_posts(keyword, num_posts)

            comments = interpreter.get_and_interpret(subreddits, keyword)

        df_ranking = postprocessing.postprocess(keyword, xref = xref)

        df_ranking.index.name = 'Brand'
        df_ranking.index = df_ranking.index.str.title()

        # Rendering...
        render_UI(df_ranking)
        #st.dataframe(df_ranking[['Sentiment']].style.format("{:.2}")) #{'Sentiment' : "{:.2}", 'Variance' : "{:.2}"})

        data_load_state.text("Results for {}:".format(keyword))
        st.write("Subreddits analyzed: {}".format(ingester.keyword_to_subreddits(keyword)))
        st.write("Comments analyzed: {}".format(df_ranking['Popularity'].sum()))

   