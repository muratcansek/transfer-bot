import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
import google.generativeai as genai # Eski ama sağlam kütüphane

# --- AI YAPILANDIRMASI (Eski Yöntem) ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# En güvenilir modeli seçiyoruz
model = genai.GenerativeModel('gemini-1.5-flash')

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def analyze_and_write(haber_basligi, takim):
    """
    Haberi analiz eder ve Türkçe tweet yazar.
    """
    prompt = f"""
    Görevin bir editör ve filtreleyici olmak.
    Haber Başlığı (İngilizce olabilir): "{haber_basligi}"
    Hedef Takım: {takim}

    Adımlar:
    1. Bu haberin ana konusu gerçekten {takim} veya {takim}'ın bir oyuncusu/transferi mi?
    2. Eğer haber başka bir takım hakkındaysa (ve {takim} sadece yan unsur ise) cevap olarak sadece "SKIP" yaz.
    3. Eğer haber {takim} hakkındaysa: Bunu mükemmel bir Türkçe ile, taraftarı heyecanlandıran, emojili bir tweet metnine çevir.
    4. KESİNLİKLE İngilizce kelime kullanma. Sadece Türkçe tweet metnini ver.
    """
    
    try:
        # Eski kütüphanenin fonksiyonu
        response = model.generate_content(prompt)
        result = response.text.strip().replace('"', '')
        
        if "SKIP" in result or len(result) < 5:
            return None
        return result
        
    except Exception as e:
        # BURASI ÇOK ÖNEMLİ: Hatanın ne olduğunu artık göreceğiz
        print(f"⚠️ AI Hatası ({takim}): {e}")
        return None

def haber_tara():
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    if salter == "KAPALI": return

    try:
        limit = int(os.environ.get("HABER_SAYISI", "1"))
    except:
        limit = 1

    takimlar = ["Fenerbahçe", "Galatasaray", "Beşiktaş", "Trabzonspor"]
    twitter_client = baglan()

    for takim in takimlar:
        print(f"🌍 {takim} için analiz başladı ({limit} haber)...")
        
        sorgu = urllib.parse.quote(f"{takim} transfer news")
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=en-US&gl=US&ceid=US:en"
        
        paylasilan_sayisi = 0
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            root = ElementTree.fromstring(response.content)
            items = root.findall('./channel/item')

            for item in items:
                if paylasilan_sayisi >= limit:
                    break

                baslik = item.find('title').text
                link = item.find('link').text
                
                # AI Analizi
                tweet_metni = analyze_and_write(baslik, takim)
                
                if tweet_metni is None:
                    # Alakasız haberleri atladığını görmek için log
                    # print(f"❌ Alakasız haber atlandı: {baslik}") 
                    continue 

                tweet_final = f"{tweet_metni}\n\n🔗 Kaynak: {link}"
                
                try:
                    twitter_client.create_tweet(text=tweet_final)
                    print(f"✅ {takim} haberi Türkçe paylaşıldı.")
                    paylasilan_sayisi += 1
                    time.sleep(15)
                except Exception as e:
                    print(f"🚨 Tweet Atma Hatası: {e}")
                
        except Exception as e:
            print(f"⚠️ {takim} genel hata: {e}")

if __name__ == "__main__":
    haber_tara()
