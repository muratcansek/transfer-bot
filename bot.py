import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse

def baglan():
    # 403 hatalarını önlemek için en stabil bağlantı yöntemi
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def haber_tara():
    # 1. ŞALTER KONTROLÜ (En başta)
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    if salter == "KAPALI":
        print("⛔ BOT DURDURULDU: GitHub Secrets üzerinden BOT_DURUMU 'KAPALI' olarak ayarlanmış.")
        return

    hedef_takim = os.environ.get("SECILEN_TAKIM", "Fenerbahçe")
    client = baglan()
    paylasildi_mi = False

    # 2. KAYNAK LİSTESİ
    kaynaklar = [
        {"ad": "TRT Spor Transfer", "url": "https://www.trtspor.com.tr/transfer-haberleri.rss"},
        {"ad": "Fanatik", "url": "https://www.fanatik.com.tr/fenerbahce/rss"},
        {"ad": "Fotomaç", "url": "https://www.fotomac.com.tr/rss/fenerbahce.xml"},
        {"ad": "Yağız Sabuncuoğlu (X)", "url": "https://nitter.poast.org/yagosabuncuoglu/rss"},
        {"ad": "Nexus Sports (X)", "url": "https://nitter.poast.org/nexussportstv/rss"}
    ]

    print(f"🔄 {hedef_takim} için tarama başladı (Şalter: {salter})...")

    # 3. KAYNAKLARI TEK TEK GEZ
    for kaynak in kaynaklar:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            response = requests.get(kaynak["url"], headers=headers, timeout=10)
            
            if response.status_code != 200:
                continue

            root = ElementTree.fromstring(response.content)
            for item in root.findall('./channel/item')[:5]:
                baslik = item.find('title').text
                link = item.find('link').text
                
                if hedef_takim.lower() in baslik.lower():
                    tweet_metni = f"🚨 {hedef_takim.upper()} SON DAKİKA\n\n{baslik}\n\n📍 Kaynak: {kaynak['ad']}\n🔗 {link}"
                    client.create_tweet(text=tweet_metni)
                    print(f"✅ Paylaşıldı: {kaynak['ad']}")
                    paylasildi_mi = True
                    return 

        except Exception as e:
            print(f"⚠️ {kaynak['ad']} kaynağında hata oluştu.")

    # 4. YEDEK PLAN (GOOGLE NEWS)
    if not paylasildi_mi:
        print("🔍 Spesifik kaynaklarda sonuç yok, Google News'e bakılıyor...")
        try:
            sorgu = urllib.parse.quote(f"{hedef_takim} transfer")
            google_url = f"https://news.google.com/rss/search?q={sorgu}&hl=tr&gl=TR&ceid=TR:tr"
            response = requests.get(google_url, timeout=10)
            root = ElementTree.fromstring(response.content)
            item = root.find('./channel/item')
            
            if item is not None:
                baslik = item.find('title').text
                link = item.find('link').text
                client.create_tweet(text=f"🚨 {hedef_takim.upper()} HABERİ\n\n{baslik}\n\n📍 Kaynak: Google News\n🔗 {link}")
                print("✅ Google News üzerinden paylaşıldı.")
        except Exception as e:
            print(f"⚠️ Google News yedeği de başarısız: {e}")

if __name__ == "__main__":
    haber_tara()
