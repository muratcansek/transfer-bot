import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai

# --- 2026 GÜNCEL YAPILANDIRMASI ---
client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def analyze_and_write(haber_basligi, takim):
    """Sadece gerçekten gerekliyse AI'yı çalıştırır."""
    prompt = f"""
    Sen profesyonel bir Türk Spor Editörüsün.
    Haber: "{haber_basligi}"
    Hedef Takım: {takim}
    
    Talimat: Bu haber {takim} hakkında bir transfer gelişmesi ise heyecanlı bir Türkçe tweet yaz (max 200 karakter). 
    Eğer konu {takim} değilse sadece 'SKIP' yaz.
    """
    try:
        # Model: gemini-2.0-flash
        response = client_ai.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        result = response.text.strip()
        return None if "SKIP" in result or len(result) < 10 else result
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
    twitter_client = baglan() if test_modu == "Gerçekten Paylaş" else None

    for takim in takimlar:
        print(f"🔍 {takim.upper()} taranıyor...")
        sorgu = urllib.parse.quote(f"{takim} transfer news")
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            root = ElementTree.fromstring(response.content)
            
            # KRİTİK: Sadece en güncel 10 habere bakıyoruz (Süreyi kısaltır)
            items = root.findall('./channel/item')[:10]

            paylasilan_sayisi = 0
            for item in items:
                if paylasilan_sayisi >= limit: break

                baslik = item.find('title').text
                link = item.find('link').text
                
                # 1. HIZLI KONTROL: Takım ismi geçmiyorsa hiç bekleme, hemen geç!
                if takim.lower() not in baslik.lower():
                    continue
                
                # 2. AKILLI BEKLEME: Sadece AI çağrısı öncesi 4 saniye bekle (Kota koruma)
                time.sleep(4) 
                
                tweet_metni = analyze_and_write(baslik, takim)
                
                if tweet_metni:
                    tweet_final = f"{tweet_metni}\n\n🔗 {link}"
                    
                    if twitter_client:
                        try:
                            twitter_client.create_tweet(text=tweet_final)
                            print(f"✅ Paylaşıldı: {takim}")
                        except Exception as te:
                            print(f"❌ Twitter Hatası: {te}")
                    else:
                        print(f"\n--- ÖN İZLEME ({takim}) ---\n{tweet_final}\n{'-'*20}")
                    
                    paylasilan_sayisi += 1
                    time.sleep(5) # Paylaşım sonrası kısa mola
                
        except Exception as e:
            print(f"⚠️ RSS Hatası: {e}")

if __name__ == "__main__":
    haber_tara()
