import streamlit as st
import pandas as pd
from PIL import Image

# Global Variables
DATE_COLUMN = "DATE"
DATA_PATH = "./data/stocks_data.xlsx"
TWEETS_PREDICTED_PATH = [
    "./data/data_model/webscraped_FMC_CORP.csv",
    "./data/data_model/webscraped_WEYERHAEUSER_CO.csv",
    "./data/data_model/webscraped_BP_PLC.csv",
]

# Layout
twt_logo = Image.open('app/images/twitter-logo.png')
st.set_page_config(
    page_title="Sentimental analysis", page_icon=twt_logo, layout="wide"
)

st.title("Sentimental analysis on tweets: 📈 or 📉 ?")
st.header("Defining bullish and bearish tendencies on stocks")

@st.cache_data
def load_predicted_data():
    returns = pd.read_excel(DATA_PATH, sheet_name="Returns", header=[5, 6]).T.iloc[
        2:, :
    ]
    returns = returns.rename(columns=returns.iloc[0])
    returns = returns.iloc[2:]
    upercase = lambda x: str(x).upper()
    returns.rename(upercase, axis="columns", inplace=True)
    returns.reset_index(inplace=True)
    returns.rename(columns={"level_0": "DATE1", "level_1": "DATE"}, inplace=True)
    returns.drop(columns="DATE1", inplace=True)
    returns[DATE_COLUMN] = pd.to_datetime(returns[DATE_COLUMN]).dt.date
    # we add fmc webscrapped data
    fmc_tweets = pd.read_csv(TWEETS_PREDICTED_PATH[0])
    fmc_tweets["company"] = "FMC CORP"
    # we add wy webscrapped data
    wy_tweets = pd.read_csv(TWEETS_PREDICTED_PATH[1])
    wy_tweets["company"] = "WEYERHAEUSER CO"
    # we add bp webscrapped data
    bp_tweets = pd.read_csv(TWEETS_PREDICTED_PATH[2])
    bp_tweets["company"] = "BP PLC"
    tweets = pd.concat([fmc_tweets, wy_tweets, bp_tweets])
    tweets["PostDate"] = pd.to_datetime(tweets["PostDate"]).dt.date
    # we add a column with the length of each tweet
    tweets["tweet_length"] = tweets["TweetText"].apply(lambda x: len(x.split()))
    return returns, tweets


returns, tweets = load_predicted_data()

stocklist = [
    "BP PLC",
    "FMC CORP",
    "WEYERHAEUSER CO",
]

df_columns_list = [
    "BP/ LN Equity",
    "FMC US Equity",
    "WY US Equity",
]

search_dictio = {}
for i, k in enumerate(df_columns_list):
    search_dictio[stocklist[i]] = k

# -- Choose stocks from stockslists
container = st.sidebar.container()
all = st.sidebar.checkbox("Select all")
if all:
    options = container.multiselect("**Select one or more options:**", stocklist, stocklist)
else:
    options =  container.multiselect("**Select one or more options:**", stocklist)


min_date = tweets["PostDate"].min()
max_date = tweets["PostDate"].max()

start_date = st.sidebar.date_input(
    "**Start date**:", min_value=min_date, max_value=max_date, value=min_date, key="start_date",
)
end_date = st.sidebar.date_input(
    "**End date:**", min_value=min_date, max_value=max_date, value=max_date, key="end_date",
)

condition1 = start_date <= tweets["PostDate"]
condition2 = tweets["PostDate"] <= end_date
mask = condition1 & condition2
filtered_tweets = tweets.loc[mask, :]

mask = filtered_tweets["company"].isin(options)
filtered_tweets = filtered_tweets.loc[mask, :]

# we select all the tweets from 2017 to 2022
tweet_list = filtered_tweets["TweetText"].tolist()
# join all tweets into a single string
tweet_string = " ".join(tweet_list)

st.write(
    "How to use it? You select a month, for example from 31-08-2022 to 29-09-2022 and the stocks in your portfolio or that you are interesed to buy."
)

st.write(
    "If the number of positive and bullish tweets is greater than the negative and bearish ones, you should buy the portfolio.")

st.write(
    "Suppose you have a monthly investment limit of 2000 dollars. The strategy is to standardize returns. If all tweets are positive or bullish, you should invest 2000 dollars in stocks for your portfolio. If only 40 percent of tweets are positive, you should invest 2000 x 40 = 800 dollars in stocks for your portfolio."
)

if len(options) > 0:
    c1, c2, c3, c4 = st.columns(4)

    st.metric(
    label=f"Number of tweets for the portfolio:",
    value=str(filtered_tweets.shape[0]),
)

    with c1:
        st.metric(
            label=f"Number of tweets bullish tweets:",
            value=str(filtered_tweets[filtered_tweets["sentiment"] == "Bullish"].shape[0]),
        )

    with c2:
        st.metric(
            label=f"Number of tweets bearish tweets:",
            value=str(filtered_tweets[filtered_tweets["sentiment"] == "Bearish"].shape[0]),
        )

    with c3:
        st.metric(
            label=f"Number of positives tweets:",
            value=str(
                filtered_tweets[filtered_tweets["sentiment_base"] == "positive"].shape[0]
            ),
        )

    with c4:
        st.metric(
            label=f"Number of negatives tweets:",
            value=str(
                filtered_tweets[filtered_tweets["sentiment_base"] == "negative"].shape[0]
            ),
        )

    st.header(f"Selected tweets for the portfolio:\n {', '.join(options)}")
    st.dataframe(filtered_tweets)

else:
    st.warning("Please select at least one stock to see the metrics.")