import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai

# --- YAPILANDIRMA ---
client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def baglan():
    # Eğer ön izleme modundaysak Twitter anahtarlarını kontrol etmeye bile gerek yok
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def analyze_and_write(haber_basligi, takim):
    # Ön filtre: Takım adı geçmiyorsa kotayı harcama
    if takim.lower() not in haber_basligi.lower():
        return None

    prompt = f"Sen bir spor editörüsün. Sadece Türkçe konuş. Haber: '{haber_basligi}'. Bu gerçekten {takim} haberi mi? Değilse 'SKIP' yaz, ilgiliyse heyecanlı bir Türkçe tweet yaz."
    
    try:
        response = client_ai.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        result = response.text.strip()
        if "SKIP" in result or len(result) < 10: return None
        return result
    except Exception as e:
        print(f"⚠️ AI Hatası: {e}")
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
    
    # Sadece 'Gerçekten Paylaş' seçilirse Twitter'a bağlan
    twitter_client = None
    if test_modu == "Gerçekten Paylaş":
        twitter_client = baglan()
        print("🚀 GERÇEK MOD: Tweetler Twitter'a gönderilecek.")
    else:
        print("🔬 ÖN İZLEME MODU: Tweetler sadece loglara yazılacak.")

    for takim in takimlar:
        print(f"\n--- {takim} Taraması Başladı ---")
        sorgu = urllib.parse.quote(f"{takim} transfer news")
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            root = ElementTree.fromstring(response.content)
            items = root.findall('./channel/item')

            paylasilan_sayisi = 0
            for item in items:
                if paylasilan_sayisi >= limit: break

                baslik = item.find('title').text
                link = item.find('link').text
                
                print(f"🔎 Analiz ediliyor: {baslik[:50]}...")
                time.sleep(12) # AI Kota koruması (429 önleyici)
                
                tweet_metni = analyze_and_write(baslik, takim)
                
                if tweet_metni:
                    tweet_final = f"{tweet_metni}\n\n🔗 {link}"
                    
                    if test_modu == "Gerçekten Paylaş":
                        try:
                            twitter_client.create_tweet(text=tweet_final)
                            print(f"✅ TWEET ATILDI: {takim}")
                        except Exception as te:
                            print(f"❌ Twitter Hatası: {te}")
                    else:
                        # ÖN İZLEME TASARIMI
                        print("\n" + "="*40)
                        print(f"📝 TWEET ÖN İZLEME ({takim})")
                        print("-" * 40)
                        print(tweet_final)
                        print("="*40 + "\n")
                    
                    paylasilan_sayisi += 1
                    time.sleep(10)
                
        except Exception as e:
            print(f"⚠️ Hata: {e}")

if __name__ == "__main__":
    haber_tara()
