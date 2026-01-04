import tweepy
import os
import requests
from xml.etree import ElementTree
import urllib.parse

def baglan():
    return tweepy.Client(
        bearer_token=os.environ["TWITTER_BEARER_TOKEN"],
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
    )

def haber_ara_ve_paylas():
    hedef_takim = os.getenv("SECILEN_TAKIM", "Fenerbahçe")
    client = baglan()
    
    # Google Haberler RSS URL'si (Seçilen takımı otomatik arar)
    # 'q=' kısmına takımı ve 'transfer' kelimesini ekleyerek arama hacmini daraltıyoruz
    sorgu = urllib.parse.quote(f"{hedef_takim} transfer")
    rss_url = f"https://news.google.com/rss/search?q={sorgu}&hl=tr&gl=TR&ceid=TR:tr"
    
    try:
        response = requests.get(rss_url)
        root = ElementTree.fromstring(response.content)
        
        # Google News'ten gelen ilk 3 habere bakalım
        for item in root.findall('./channel/item')[:3]:
            baslik = item.find('title').text
            link = item.find('link').text
            kaynak = item.find('source').text if item.find('source') is not None else "Haber Kaynağı"
            
            # Daha güzel bir tweet formatı
            tweet_metni = (
                f"🚨 SON DAKİKA: {hedef_takim.upper()}\n\n"
                f"📰 {baslik}\n\n"
                f"📍 Kaynak: {kaynak}\n"
                f"🔗 {link}"
            )
            
            # Tweet at
            client.create_tweet(text=tweet_metni)
            print(f"Başarıyla paylaşıldı: {baslik}")
            return # Sadece en güncel haberi atıp çıkalım
            
        print(f"Maalesef {hedef_takim} için yeni bir haber bulunamadı.")
        
    except Exception as e:
        print(f"Hata detayı: {e}")

if __name__ == "__main__":
    haber_ara_ve_paylas()
