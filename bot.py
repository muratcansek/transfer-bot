import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai

# --- 2026 YAPILANDIRMASI ---
client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def analyze_and_write(haber_basligi, takim):
    """Kota dolduğunda beklemek yerine hata döndüren hızlı analiz."""
    prompt = f"Sen bir spor editörüsün. Haber: '{haber_basligi}'. Bu {takim} transfer haberi mi? Öyleyse Türkçe tweet yaz, değilse 'SKIP' yaz."
    
    try:
        response = client_ai.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        result = response.text.strip()
        return None if "SKIP" in result or len(result) < 10 else result
    except Exception as e:
        if "429" in str(e):
            print(f"🛑 KOTA DOLU: {takim} için bu haber atlanıyor.")
        else:
            print(f"⚠️ AI Hatası: {e}")
        return None

def haber_tara():
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    test_modu = os.environ.get("TEST_MODU", "Ön İzleme (Tweet Atma)")
    if salter == "KAPALI": return

    limit = int(os.environ.get("HABER_SAYISI", "1"))
    takimlar = ["Fenerbahçe", "Galatasaray", "Beşiktaş", "Trabzonspor"]
    twitter_client = baglan() if test_modu == "Gerçekten Paylaş" else None

    for takim in takimlar:
        print(f"🔍 {takim.upper()} taranıyor...")
        sorgu = urllib.parse.quote(f"{takim} transfer news")
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            root = ElementTree.fromstring(response.content)
            # Sadece en güncel 5 habere bakarak süreyi kısaltıyoruz
            items = root.findall('./channel/item')[:5]

            paylasilan_sayisi = 0
            for item in items:
                if paylasilan_sayisi >= limit: break

                baslik = item.find('title').text
                link = item.find('link').text
                
                # ÖN FİLTRE: Takım ismi geçmiyorsa AI'yı hiç çağırma
                if takim.lower() not in baslik.lower():
                    continue
                
                # Kota sağlığı için her AI isteği öncesi kısa bir mola
                time.sleep(5)
                
                tweet_metni = analyze_and_write(baslik, takim)
                
                if tweet_metni:
                    tweet_final = f"{tweet_metni}\n\n🔗 {link}"
                    if twitter_client:
                        twitter_client.create_tweet(text=tweet_final)
                        print(f"✅ {takim} paylaşıldı.")
                    else:
                        print(f"\n--- ÖN İZLEME ({takim}) ---\n{tweet_final}\n")
                    
                    paylasilan_sayisi += 1
                    time.sleep(10) # Paylaşım sonrası kısa mola
                
        except Exception as e:
            print(f"⚠️ RSS Hatası: {e}")

if __name__ == "__main__":
    haber_tara()
