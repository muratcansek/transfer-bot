import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse

# --- TWITTER BAĞLANTISI ---
def baglan():
    return tweepy.Client(
        bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"),
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def haber_tara():
    hedef_takim = os.getenv("SECILEN_TAKIM", "Fenerbahçe")
    client = baglan()
    paylasildi_mi = False

    # --- GÜNCEL KAYNAK HAVUZU ---
    # Not: Nitter (X köprüleri) bazen IP engeli yiyebilir, bu yüzden en stabil olanları ekledim.
    kaynaklar = [
        {"ad": "TRT Spor Transfer", "url": "https://www.trtspor.com.tr/transfer-haberleri.rss"},
        {"ad": "Fanatik", "url": "https://www.fanatik.com.tr/fenerbahce/rss"},
        {"ad": "Fotomaç", "url": "https://www.fotomac.com.tr/rss/fenerbahce.xml"},
        {"ad": "Yağız Sabuncuoğlu (X)", "url": "https://nitter.poast.org/yagosabuncuoglu/rss"},
        {"ad": "Nexus Sports (X)", "url": "https://nitter.poast.org/nexussportstv/rss"}
    ]

    print(f"🔄 {hedef_takim} haberleri için tarama başlıyor...")

    # 1. ADIM: Spesifik Kaynakları Tara
    for kaynak in kaynaklar:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
            response = requests.get(kaynak["url"], headers=headers, timeout=10)
            
            if response.status_code != 200:
                continue

            root = ElementTree.fromstring(response.content)
            for item in root.findall('./channel/item')[:5]:
                baslik = item.find('title').text
                link = item.find('link').text
                
                # Filtreleme
                if hedef_takim.lower() in baslik.lower():
                    tweet_metni = f"🚨 {hedef_takim.upper()} SON DAKİKA\n\n{baslik}\n\n📍 Kaynak: {kaynak['ad']}\n🔗 {link}"
                    client.create_tweet(text=tweet_metni)
                    print(f"✅ Paylaşıldı: {kaynak['ad']}")
                    paylasildi_mi = True
                    return # Bir tane bulunca dur

        except Exception as e:
            print(f"⚠️ {kaynak['ad']} taranırken hata oluştu, sıradakine geçiliyor...")

    # 2. ADIM: Yedek Plan (Google News)
    # Eğer yukarıdaki kaynaklar hata verirse veya haber bulamazsa burası devreye girer.
    if not paylasildi_mi:
        print("🔍 Spesifik kaynaklarda haber bulunamadı, Google News taranıyor...")
        try:
            sorgu = urllib.parse.quote(f"{hedef_takim} transfer")
            google_url = f"https://news.google.com/rss/search?q={sorgu}&hl=tr&gl=TR&ceid=TR:tr"
            
            response = requests.get(google_url, timeout=10)
            root = ElementTree.fromstring(response.content)
            item = root.find('./channel/item')
            
            if item is not None:
                baslik = item.find('title').text
                link = item.find('link').text
                tweet_metni = f"🚨 {hedef_takim.upper()} HABERİ\n\n{baslik}\n\n📍 Kaynak: Google News\n🔗 {link}"
                client.create_tweet(text=tweet_metni)
                print("✅ Google News üzerinden paylaşıldı.")
            else:
                print("❌ Hiçbir kaynakta yeni haber bulunamadı.")
        except Exception as e:
            print(f"⚠️ Yedek plan da başarısız oldu: {e}")

if __name__ == "__main__":
    haber_tara()
