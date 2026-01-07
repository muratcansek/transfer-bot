import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai

# --- AI BAĞLANTISI ---
# 404 hatasını önlemek için Client'ı en sade haliyle başlatıyoruz
try:
    client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception as e:
    print(f"❌ Gemini Client başlatılamadı: {e}")
    client_ai = None

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def analyze_and_write(haber_basligi, takim):
    """
    Haber analizini yapar. 404 hatasını önlemek için model ismini
    net bir şekilde 'gemini-1.5-flash' olarak kullanır.
    """
    if not client_ai:
        return None

    prompt = f"""
    Sen bir spor editörüsün. Sadece Türkçe konuş.
    Haber: "{haber_basligi}"
    Bu haber gerçekten {takim} transferi/haberi mi?
    - Eğer değilse sadece 'SKIP' yaz.
    - Eğer ilgiliyse, haberi Türkçeye çevir ve taraftarlar için heyecanlı, 
      maksimum 200 karakterlik, emojili bir tweet yaz.
    """
    
    try:
        # Yeni SDK'da en stabil model çağırma yöntemi
        response = client_ai.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        
        result = response.text.strip()
        
        if "SKIP" in result or len(result) < 10:
            return None
            
        return result

    except Exception as e:
        # Hata devam ederse burası detaylı bilgi verecek
        print(f"⚠️ AI Analiz Hatası ({takim}): {e}")
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
        print(f"🌍 {takim} taranıyor...")
        sorgu = urllib.parse.quote(f"{takim} transfer news")
        # Global arama
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
                    try:
                        twitter_client.create_tweet(text=tweet_final)
                        print(f"✅ {takim} Tweetlendi.")
                        paylasilan_sayisi += 1
                        time.sleep(20)
                    except Exception as e:
                        print(f"❌ Twitter Hatası: {e}")
                
        except Exception as e:
            print(f"⚠️ {takim} RSS Hatası: {e}")

if __name__ == "__main__":
    haber_tara()
