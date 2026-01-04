import tweepy
import os

client = tweepy.Client(
    consumer_key=os.environ["TWITTER_API_KEY"],
    consumer_secret=os.environ["TWITTER_API_SECRET"],
    access_token=os.environ["TWITTER_ACCESS_TOKEN"],
    access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
)

try:
    client.create_tweet(text="Bu bir bağlantı testidir! 🚀")
    print("Tweet başarıyla atıldı!")
except Exception as e:
    print(f"Hata detayı: {e}")
