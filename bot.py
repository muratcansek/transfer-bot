import tweepy
import os
import requests
import time
from xml.etree import ElementTree

# --- AYARLAR VE BAĞLANTI ---
def baglan():
    # .env dosyasından veya sistem değişkenlerinden gelen anahtarlar
    return tweepy.Client(
        bearer_token=os.environ.get("TWITTER_BEARER_TOKEN"),
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def haber_tara():
    # Takım ismini burada belirle (veya sistem değişkeninden al)
    hedef_takim = os.getenv("SECILEN_TAKIM", "Fenerbahçe")
    client = baglan()

    # --- KAYNAK HAVUZU ---
    # Hem web sitelerini hem de takip etmek istediğin Twitter hesaplarını ekliyoruz.
    # Twitter hesapları için 'xcancel.com' veya 'nitter.poast.org' gibi çalışan köprüleri kullanıyoruz.
    kaynaklar = [
        # Web Siteleri
        {"ad": "TRT Spor", "url": "https://www.trtspor.com.tr/haber-akisi.rss"},
        {"ad": "A Spor", "url": "https://www.aspor.com.tr/rss/ana-sayfa.xml"},
        
        # Twitter Hesapları (Nitter/XCancel üzerinden)
        # Örnek: Yağız Sabuncuoğlu (@yagosabuncuoglu) takibi için:
        {"ad": "Yağız Sabuncuoğlu (X)", "url": "https://xcancel.com/yagosabuncuoglu/rss"},
        {"ad": "Fabrizio Romano (X)", "url": "https://xcancel.com/FabrizioRomano/rss"},
        {"ad": "Transfer Merkezi (X)", "url": "https://xcancel.com/transfermerkez/rss"}
    ]

    print(f"🔄 {hedef_takim} haberleri için {len(kaynaklar)} kaynak taranıyor...")

    for kaynak in kaynaklar:
        try:
            # Botun gerçek bir kullanıcı gibi görünmesi için Header ekliyoruz
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(kaynak["url"], headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ {kaynak['ad']} kaynağına erişilemedi (Kod: {response.status_code})")
                continue

            root = ElementTree.fromstring(response.content)
            
            # Kaynaktaki son 5 öğeyi kontrol et
            for item in root.findall('./channel/item')[:5]:
                baslik = item.find('title').text
                link = item.find('link').text
                
                # Arama Filtresi: Hem takım ismi hem de 'transfer' veya 'sıcak' gibi kelimeler geçiyor mu?
                # (Sadece takım ismi geçmesi yeterli dersen 'and' kısmını silebilirsin)
                if hedef_takim.lower() in baslik.lower():
                    tweet_metni = (
                        f"🚨 {hedef_takim.upper()} SON DAKİKA\n\n"
                        f"{baslik}\n\n"
                        f"📍 Kaynak: {kaynak['ad']}\n"
                        f"🔗 {link}"
                    )
                    
                    # Tweet atma işlemi
                    client.create_tweet(text=tweet_metni)
                    print(f"✅ Paylaşıldı: {baslik[:50]}...")
                    
                    # Twitter API sınırlarına takılmamak ve flood yapmamak için 10 saniye bekle
                    time.sleep(10)
                    return # Her çalıştığında sadece en güncel 1 haberi paylaşması için

        except Exception as e:
            print(f"⚠️ {kaynak['ad']} taranırken bir hata oluştu: {e}")

if __name__ == "__main__":
    haber_tara()
