import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai
from google.genai import errors # Hata yakalamak için gerekli

# --- 2026 GÜNCEL YAPILANDIRMASI ---
client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def analyze_and_write(haber_basligi, takim, deneme_sayisi=0):
    """Kota dostu ve hata durumunda bekleyip tekrar deneyen analiz fonksiyonu."""
    
    if deneme_sayisi > 2: # En fazla 2 kez tekrar dene
        return None

    prompt = f"Sen bir spor editörüsün. Haber: '{haber_basligi}'. Bu gerçekten {takim} transfer haberi mi? Değilse 'SKIP', ilgiliyse Türkçe tweet yaz."
    
    # Denenecek model listesi (Flash dolarsa Lite sürümünü dene)
    modeller = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]

    try:
        # Önce ana modeli dene
        response = client_ai.models.generate_content(
            model=modeller[0], 
            contents=prompt
        )
        result = response.text.strip()
        return None if "SKIP" in result or len(result) < 10 else result

    except Exception as e:
        hata_mesaji = str(e)
        if "429" in hata_mesaji or "RESOURCE_EXHAUSTED" in hata_mesaji:
            print(f"⏳ Kota doldu, 40 saniye bekleniyor... (Deneme: {deneme_sayisi + 1})")
            time.sleep(40) # Hata mesajındaki 'retry in 37s' uyarısına uyuyoruz
            return analyze_and_write(haber_basligi, takim, deneme_sayisi + 1)
        
        elif "503" in hata_mesaji:
            print("⚠️ Model meşgul, 10 saniye sonra tekrar denenecek...")
            time.sleep(10)
            return analyze_and_write(haber_basligi, takim, deneme_sayisi + 1)
        
        print(f"⚠️ Beklenmedik AI Hatası: {e}")
        return None

def haber_tara():
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    test_modu = os.environ.get("TEST_MODU", "Ön İzleme (Tweet Atma)")
    if salter == "KAPALI": return

    try:
        limit = int(os.environ.get("HABER_SAYISI", "1"))
    except:
        limit = 1

    takimlar = ["Fenerbahçe", "Galatasaray", "Beşiktaş", "Trabzonspor"]
    twitter_client = baglan() if test_modu == "Gerçekten Paylaş" else None

    for takim in takimlar:
        print(f"🔍 {takim.upper()} taranıyor...")
        sorgu = urllib.parse.quote(f"{takim} transfer news")
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            root = ElementTree.fromstring(response.content)
            items = root.findall('./channel/item')[:8] # Sadece en güncel 8 habere bak

            paylasilan_sayisi = 0
            for item in items:
                if paylasilan_sayisi >= limit: break

                baslik = item.find('title').text
                link = item.find('link').text
                
                # ÖN FİLTRE: Takım adı geçmiyorsa API'yi hiç çağırma (KOTAYI KORUR)
                if takim.lower() not in baslik.lower():
                    continue
                
                # AI'yı çağırmadan önce her seferinde kısa bir mola (Dakikalık kotayı korur)
                time.sleep(5)
                
                tweet_metni = analyze_and_write(baslik, takim)
                
                if tweet_metni:
                    tweet_final = f"{tweet_metni}\n\n🔗 {link}"
                    
                    if twitter_client:
                        twitter_client.create_tweet(text=tweet_final)
                        print(f"✅ Paylaşıldı: {takim}")
                    else:
                        print(f"\n--- ÖN İZLEME ({takim}) ---\n{tweet_final}\n{'-'*20}")
                    
                    paylasilan_sayisi += 1
                    # Paylaşımdan sonra uzun mola (Kotayı dengeler)
                    print("😴 Kota sağlığı için 30 saniye dinleniliyor...")
                    time.sleep(30)
                
        except Exception as e:
            print(f"⚠️ Hata: {e}")

if __name__ == "__main__":
    haber_tara()
