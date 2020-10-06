import sys
sys.path.append("..")
import streamlit as st 
import pandas as pd

from crowdrank import ingester
from crowdrank import interpreter
from crowdrank import postprocessing



#Input subreddit:
def orchestrate():
    subreddit = "wow"

    #reddata_getter.get_recent_posts([subreddit])
    # This should skip if the data already exists...

    # Time to run these is under 1 min
    interpreter.get_and_interpret(subreddit)
    print("Done interpreting")
    ranking = postprocessing.postprocess(subreddit)

if __name__=='__main__':
    print("ok")
    st.title("AskReddit")
    subreddit = st.sidebar.text_input("Enter subreddit")
    # subreddit = st.sidebar.selectbox('Which subreddit?', ('headphoneadvice', 'BuildaPC', 'Smartphones'))

    xref_response = st.sidebar.selectbox('Cross-reference brands?', ('Yes', 'No'))
    xref = (xref_response == 'Yes')
    if subreddit != "":
        
        data_load_state = st.text("Loading Reddit data...")
        num_posts = 500
        out_file = ingester.get_recent_posts([subreddit], num_posts)
        comments = interpreter.get_and_interpret(subreddit)
        
        df_ranking = postprocessing.postprocess(subreddit, xref = xref)
        print(df_ranking)
        st.write(df_ranking)

        #st.table(df)
        data_load_state.text("Done interpreting comments from {}".format(subreddit))

   