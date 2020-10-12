import sys
sys.path.append("..")
import os.path
import streamlit as st 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time



def pie_plot(df_ranking):
    # Courtesy of matplotlib.org...
    # Pie chart, slices are ordered and plotted counter-clockwise:
    labels = df_ranking.index 
    sizes = df_ranking.Popularity.values 
    fig1, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.f%%', startangle=75)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    st.pyplot()

def clean_for_pie(df_ranking):
    df_ranking = df_ranking.sort_values(by=['Popularity'])
    mask = df_ranking['Popularity'] > 0.02*df_ranking['Popularity'].sum()
    #other_perc = df_ranking[~mask]['Popularity'].sum()
    #df_ranking['Other'] = [0, other_perc, 0]
    df_ranking = df_ranking[mask]
    return df_ranking

def bar_plot(df_ranking):
    fig, ax = plt.subplots(figsize = (10,3))
    sns.barplot(x=df_ranking.index, y='Sentiment', data=df_ranking, ax = ax)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    ax.tick_params(axis='both', which='major', pad=15)
    ax.xaxis.labelpad = 5
    ax.yaxis.labelpad = 5
    st.pyplot()

def my_autopct(pct):
    return ('%1.f%%' % pct) if pct > 3 else ''

def combined_plot(df_ranking):
    # Plots a community sentiment barplot and number of voters piechart
    fig, axs = plt.subplots(1, 2, figsize = (12, 5))
    
    plt.subplots_adjust(wspace=0.35)
    plt.rcParams.update({'font.size': 15})
    df_ranking = df_ranking.sort_values(by=['Sentiment'], ascending=False)
    sns.barplot(x = 'Sentiment', y = df_ranking.index, data=df_ranking, ax = axs[0],
    palette = sns.color_palette(df_ranking['Color'].values))
    axs[0].set_yticklabels(axs[0].get_yticklabels(), fontsize=19)
    axs[0].tick_params(axis="x", labelsize=15)
    axs[0].tick_params(axis='both', which='major', pad=6)
    axs[0].xaxis.labelpad = 7
    axs[0].yaxis.labelpad = 7
    axs[0].yaxis.label.set_visible(False)
    axs[0].set_xlabel("Community Score", fontsize= 25, labelpad=24)
    axs[0].xaxis.set_ticks_position("top")
    axs[0].xaxis.set_label_position('top') 
    
    # Make for pie chart
    df_ranking = df_ranking.sort_values(by=['Popularity'], ascending = False)
    labels = [n if v > df_ranking['Popularity'].sum() * 0.04 else ''
              for n, v in zip(df_ranking.index, df_ranking['Popularity'].values)] 
    patches, texts, autotexts = axs[1].pie(df_ranking.Popularity.values, labels = labels,
                                            autopct= my_autopct, startangle=75,
                                            colors = df_ranking['Color'].values)
    unused = [ _.set_fontsize(15) for _ in texts]
    axs[1].axis('equal')
    axs[1].set_title('Percent of Mentions', pad=52, fontsize=25)
    
    st.pyplot()