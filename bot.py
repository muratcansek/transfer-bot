import tweepy
import os
import requests
from xml.etree import ElementTree

def baglan():
    return tweepy.Client(
        bearer_token=os.environ["TWITTER_BEARER_TOKEN"],
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
    )

def haberleri_tara():
    # Arayüzden gelen ayarları oku
    hedef_takim = os.getenv("SECILEN_TAKIM", "Fenerbahçe")
    limit = int(os.getenv("HABER_SAYISI", "5"))
    
    print(f"🔍 {hedef_takim} için son {limit} haber taranıyor...")
    
    client = baglan()
    rss_url = "https://www.trtspor.com.tr/haber-akisi.rss"
    
    try:
        response = requests.get(rss_url)
        root = ElementTree.fromstring(response.content)
        
        for item in root.findall('./channel/item')[:limit]:
            baslik = item.find('title').text
            link = item.find('link').text
            
            # Eğer seçilen takım başlıkta geçiyorsa
            if hedef_takim.lower() in baslik.lower():
                tweet_metni = f"🚨 {hedef_takim.upper()} TRANSFER HABERİ\n\n📌 {baslik}\n\n🔗 Detay: {link}"
                client.create_tweet(text=tweet_metni)
                print(f"✅ Paylaşıldı: {baslik}")
                return # Bir seferde sadece en güncel 1 taneyi paylaş
                
        print("❌ Uygun yeni haber bulunamadı.")
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    haberleri_tara()
