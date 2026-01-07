import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
import google.generativeai as genai # Eski dostumuz geri döndü

# --- AI YAPILANDIRMASI (STABİL VERSİYON) ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Model tanımlamasını burada yapıyoruz, en güncel flash modelini seçiyoruz
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
    Haber analizi ve Türkçe çeviri yapar.
    """
    prompt = f"""
    Sen bir spor editörüsün.
    Haber Başlığı: "{haber_basligi}"
    Hedef Takım: {takim}

    Kurallar:
    1. Bu haber {takim} ile ilgili mi? Değilse sadece "SKIP" yaz.
    2. İlgiliyse, haberi Türkçeye çevir ve {takim} taraftarı için heyecanlı bir tweet yaz.
    3. İngilizce tek bir kelime bile kullanma.
    4. Maksimum 200 karakter.
    """
    
    try:
        # Eski kütüphanenin basit kullanım şekli
        response = model.generate_content(prompt)
        result = response.text.strip().replace('"', '')
        
        if "SKIP" in result or len(result) < 5:
            return None
        return result
            
    except Exception as e:
        # Hata detayını tam görelim
        print(f"❌ AI Hatası (Detaylı): {e}")
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
        print(f"🌍 {takim} analiz ediliyor...")
        
        # İngilizce kaynakları tara
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
                
                tweet_metni = analyze_and_write(baslik, takim)
                
                if tweet_metni:
                    tweet_final = f"{tweet_metni}\n\n🔗 Kaynak: {link}"
                    twitter_client.create_tweet(text=tweet_final)
                    print(f"✅ {takim}: {tweet_metni[:30]}...")
                    paylasilan_sayisi += 1
                    time.sleep(15)
                else:
                    print(f"⏭️ {takim} için bu haber geçildi (Alakasız/AI Skip).")
                
        except Exception as e:
            print(f"⚠️ {takim} bağlantı hatası: {e}")

if __name__ == "__main__":
    haber_tara()
