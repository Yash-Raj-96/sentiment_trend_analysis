import tweepy
import pandas as pd
import re
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import os
import time
import datetime

# Twitter API authentication
def authenticate_twitter_api():
    bearer_token = "YOUR_BEARER_TOKEN_HERE"
    client = tweepy.Client(bearer_token=bearer_token)
    return client

# Fetch tweets with rate-limit handling and pagination
def fetch_tweets(client, query, max_results=200):
    tweet_data = []
    next_token = None
    fetched = 0
    print(f"Starting fetch of up to {max_results} tweets...")

    while fetched < max_results:
        try:
            batch_size = min(100, max_results - fetched)  # 100 is Twitter’s max per request
            response = client.search_recent_tweets(
                query=query,
                max_results=batch_size,
                tweet_fields=['created_at', 'text'],
                next_token=next_token
            )
            if response.data:
                for tweet in response.data:
                    tweet_data.append({
                        'tweet': tweet.text,
                        'created_at': tweet.created_at
                    })
                fetched += len(response.data)
                print(f"Fetched {fetched} tweets so far...")
                next_token = response.meta.get('next_token')
                if not next_token:
                    break
            else:
                break  # No more data
        except tweepy.TooManyRequests:
            print("Rate limit hit. Sleeping for 15 minutes...")
            time.sleep(15 * 60)
        except Exception as e:
            print(f"Error occurred: {e}")
            break

    print(f"Finished fetching {len(tweet_data)} tweets.")
    return pd.DataFrame(tweet_data)

# Clean tweet text
def clean_tweet(tweet):
    tweet = re.sub(r"http\S+", "", tweet)
    tweet = re.sub(r"@\S+", "", tweet)
    tweet = re.sub(r"#", "", tweet)
    tweet = re.sub(r"[^A-Za-z0-9\s]", "", tweet)
    tweet = re.sub(r"\n", " ", tweet)
    return tweet.strip()

# Sentiment analysis
def get_sentiment(tweet):
    return TextBlob(tweet).sentiment.polarity

def categorize_sentiment(score):
    if score > 0:
        return 'Positive'
    elif score < 0:
        return 'Negative'
    else:
        return 'Neutral'

# Plot sentiment pie chart
def plot_sentiment_pie(df):
    sentiment_counts = df['sentiment_category'].value_counts()
    sentiment_counts.plot.pie(
        autopct='%1.1f%%', 
        colors=['lightgreen', 'lightcoral', 'skyblue'], 
        figsize=(7,7)
    )
    plt.title("Sentiment Distribution")
    plt.ylabel("")
    plt.show()

# Plot word cloud
def plot_wordcloud(df):
    all_text = " ".join(df['cleaned_tweet'])
    wordcloud = WordCloud(width=800, height=500, background_color='white').generate(all_text)
    plt.figure(figsize=(10,6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title("Trending Words WordCloud")
    plt.show()

# Plot top hashtags bar chart
def plot_top_hashtags(df):
    hashtags = []
    for tweet in df['tweet']:
        hashtags.extend(re.findall(r"#(\w+)", tweet))
    if hashtags:
        hashtag_freq = pd.Series(hashtags).value_counts().head(10)
        hashtag_freq.plot(kind='bar', color='skyblue')
        plt.title("Top 10 Trending Hashtags")
        plt.xlabel("Hashtag")
        plt.ylabel("Frequency")
        plt.show()
    else:
        print("No hashtags found in tweets.")

# Main function
def main():
    # Make sure output directory exists
    os.makedirs('data', exist_ok=True)

    client = authenticate_twitter_api()
    query = "weather OR climate OR storm OR flood OR rainfall -is:retweet lang:en"

    print("Fetching tweets...")
    df_tweets = fetch_tweets(client, query, max_results=200)

    if df_tweets.empty:
        print("No tweets fetched. Exiting.")
        return

    # Clean, analyze, and categorize
    df_tweets['cleaned_tweet'] = df_tweets['tweet'].apply(clean_tweet)
    df_tweets['sentiment_score'] = df_tweets['cleaned_tweet'].apply(get_sentiment)
    df_tweets['sentiment_category'] = df_tweets['sentiment_score'].apply(categorize_sentiment)

    # Save CSV with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"data/tweets_data_{timestamp}.csv"
    df_tweets.to_csv(filename, index=False)
    print(f"Saved tweets to {filename}")

    # Visualizations
    plot_sentiment_pie(df_tweets)
    plot_wordcloud(df_tweets)
    plot_top_hashtags(df_tweets)

    print("Sentiment analysis and trend detection completed!")

if __name__ == '__main__':
    main()
