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

def haber_bul_ve_paylas(takim):
    client = baglan()
    # TRT Spor RSS kaynağını kullanıyoruz (ücretsiz ve hızlıdır)
    rss_url = "https://www.trtspor.com.tr/haber-akisi.rss"
    
    try:
        response = requests.get(rss_url)
        root = ElementTree.fromstring(response.content)
        
        found = False
        for item in root.findall('./channel/item'):
            baslik = item.find('title').text
            link = item.find('link').text
            
            # Seçilen takım başlıkta geçiyor mu kontrol et
            if takim == "Hepsi" or takim.lower() in baslik.lower():
                # Tweet formatını belirliyoruz
                tweet_metni = f"🚨 {takim.upper()} TRANSFER HABERİ\n\n📌 {baslik}\n\n🔗 Detaylar: {link}"
                
                client.create_tweet(text=tweet_metni)
                print(f"Başarıyla paylaşıldı: {baslik}")
                found = True
                break # Tek seferde çok tweet atmaması için durduruyoruz
        
        if not found:
            print(f"{takim} ile ilgili güncel haber bulunamadı.")
            
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    # GitHub arayüzünden seçilen takımı al, seçilmemişse "Fenerbahçe" varsay
    hedef_takim = os.getenv("SECILEN_TAKIM", "Fenerbahçe")
    print(f"İşlem başlatılıyor: {hedef_takim}")
    haber_bul_ve_paylas(hedef_takim)
