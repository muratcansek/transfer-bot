import tweepy
import os

# GitHub Secrets'tan bilgileri çekiyoruz
api_key = os.environ["TWITTER_API_KEY"]
api_secret = os.environ["TWITTER_API_SECRET"]
access_token = os.environ["TWITTER_ACCESS_TOKEN"]
access_token_secret = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

# Twitter bağlantısı
client = tweepy.Client(
    consumer_key=api_key, consumer_secret=api_secret,
    access_token=access_token, access_token_secret=access_token_secret
)

def tweet_at():
    # Buraya ileride haber çekme mantığını ekleyeceğiz
    haber = "Test: 4 Büyükler transfer botu çalışıyor! ⚽"
    try:
        client.create_tweet(text=haber)
        print("Tweet başarıyla atıldı!")
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    tweet_at()
