import sys
sys.path.append("..")
import os.path
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from crowdrank import ingester
from crowdrank import interpreter
from crowdrank import postprocessing
from crowdrank import visualizer


def handle_input():
    # Handle user input (string keyword, boolean x-ref)
    keyword = st.sidebar.selectbox(
        "What type of product are you looking for?",
        (
            "",
            "Headphones",
            "Laptops",
            "Computers",
            "Keyboards",
            "Mouses",
            "Monitors",
            "Tvs",
            "Tablets",
            "Smartwatches",
        ),
    )

    xref_response = st.sidebar.selectbox("Cross-reference brands?", ("Yes", "No"))
    xref = xref_response == "Yes"
    recollect = st.sidebar.selectbox('Get new data?', ('No', 'Yes'))
    return keyword, xref, recollect == 'Yes'


def render_UI(df_ranking, keyword):
    df_ranking = df_ranking.sort_values(by=["Popularity"], ascending=False)
    if len(df_ranking) >= 8:
        df_ranking = df_ranking.iloc[:8]
    sns.set_theme()
    sns.set_style("darkgrid")
    df_ranking["Color"] = [i for i in sns.color_palette().as_hex()[:len(df_ranking)]]

    visualizer.combined_plot(df_ranking)


def load_page(keyword, xref, skip):
    status_text = st.empty()
    progress_bar = st.progress(0)

    if keyword != "":

        status_text.text("Loading Reddit Data...")
        progress_bar.progress(33)
        time.sleep(0.1)

        # If results exist, skip ingestion
        subreddits = ingester.get_recent_posts(keyword, num_posts=500, skip = skip)
        progress_bar.progress(60)
        status_text.text("Interpreting...")
        # For 15,000 --> 5 mins
        comments = interpreter.get_and_interpret(subreddits, keyword)

        progress_bar.progress(80)
        time.sleep(0.1)
        status_text.text("Processing...")

        df_ranking = postprocessing.postprocess(keyword, xref=xref)
        df_ranking.index.name = "Brand"
        df_ranking.index = df_ranking.index.str.title()
        print(df_ranking)

        progress_bar.progress(100)
        time.sleep(0.1)
        status_text.empty()
        progress_bar.empty()

        # Render visualizations
        render_UI(df_ranking, keyword)

        # Extra info
        st.markdown("---")
        subreddits = [sr.capitalize() for sr in ingester.keyword_to_subreddits(keyword)]
        st.write("Subreddits analyzed: {}".format(", ".join(subreddits)))
        st.write(
            "Comments analyzed: {}".format(
                sum([ingester.count_comments(sr.lower(), 360) for sr in subreddits])
            )
        )
        # st.write("Top 5 brands: {}".format(", ".join(df_ranking.iloc[:5].index.values))


if __name__ == "__main__":
    st.markdown(
        "<h1 style='text-align: center; color: black;'> CrowdRank </h1>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.set_option("deprecation.showPyplotGlobalUse", False)

    keyword, xref, recollect = handle_input()
    skip = not recollect
    load_page(keyword, xref, skip)

