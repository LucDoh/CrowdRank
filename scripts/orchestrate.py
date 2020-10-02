import sys
sys.path.append("..")
import streamlit as st
import pandas as pd

from csp_sentiment import reddata_getter
from csp_sentiment import interpreter
from csp_sentiment import postprocessing



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
    if subreddit != "":
        # subreddit = st.sidebar.selectbox('Which subreddit?', ('headphoneadvice', 'BuildaPC', 'Smartphones'))
        data_load_state = st.text("Loading Reddit data...")
        num_posts = 10
        out_file = reddata_getter.get_recent_posts([subreddit], num_posts)
        comments = interpreter.get_and_interpret(subreddit)
        #ranking = postprocessing.postprocess(subreddit)

        st.write(comments)

        #st.table(df)
    data_load_state.text("Done interpreting comments from {}".format(subreddit))

   