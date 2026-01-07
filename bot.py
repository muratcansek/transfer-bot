import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai

# --- 2026 MODEL YAPILANDIRMASI ---
# Gemini 2.5 Flash ücretsiz kota: Dakikada 5 istek.
client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def analyze_and_write(haber_basligi, takim):
    """Kota dostu analiz fonksiyonu."""
    
    # 1. ÖN FİLTRE: Haber başlığında takım adı geçmiyorsa Gemini'yi yorma (Kota tasarrufu)
    if takim.lower() not in haber_basligi.lower():
        return None

    prompt = f"""
    Sen bir spor editörüsün. Sadece Türkçe konuş.
    Haber: "{haber_basligi}"
    Bu haber gerçekten {takim} transferi/haberi mi?
    - Eğer değilse sadece 'SKIP' yaz.
    - Eğer ilgiliyse, haberi Türkçeye çevir ve taraftarlar için heyecanlı bir tweet yaz (max 200 karakter).
    """
    
    try:
        # 2026'nın güncel model ismi: gemini-2.5-flash
        response = client_ai.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        
        result = response.text.strip()
        if "SKIP" in result or len(result) < 10:
            return None
            
        return result

    except Exception as e:
        print(f"⚠️ Gemini Kota/Hız Sınırı: {e}")
        # Hata 429 ise biraz daha beklemesi için sinyal veriyoruz
        time.sleep(35) 
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
        print(f"🔄 {takim} inceleniyor...")
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
                
                # Gemini'ye sormadan önce bekle (Dakikada 5 sınırı için)
                print("⏳ AI analizi için bekleniyor...")
                time.sleep(15) 
                
                tweet_metni = analyze_and_write(baslik, takim)
                
                if tweet_metni:
                    try:
                        tweet_final = f"{tweet_metni}\n\n🔗 {link}"
                        twitter_client.create_tweet(text=tweet_final)
                        print(f"✅ {takim} paylaşıldı.")
                        paylasilan_sayisi += 1
                        # Twitter limiti için bekle
                        time.sleep(20)
                    except Exception as te:
                        if "429" in str(te):
                            print("❌ Twitter günlük tweet sınırına ulaşıldı!")
                            return # Twitter sınırı dolduysa botu tamamen durdur
                        print(f"❌ Twitter Hatası: {te}")
                
        except Exception as e:
            print(f"⚠️ RSS Hatası ({takim}): {e}")

if __name__ == "__main__":
    haber_tara()
