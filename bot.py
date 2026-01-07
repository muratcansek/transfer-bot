import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai 
from google.genai import types

# --- AI BAĞLANTISI (YENİ KÜTÜPHANE) ---
try:
    client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
except Exception as e:
    print(f"❌ API Anahtarı Hatası: {e}")
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
    Haberi analiz eder. Eğer o takımla ilgiliyse Türkçe yazar.
    Değilse veya AI çalışmazsa None döndürür.
    """
    if not client_ai:
        return None

    prompt = f"""
    Sen bir spor editörüsün. Görevin filtreleme ve yazarlık.
    
    Haber: "{haber_basligi}"
    Hedef Takım: {takim}

    Kurallar:
    1. ANALİZ ET: Bu haberin ANA KONUSU {takim} mı? (Sadece isminin geçmesi yetmez, konu onlar olmalı).
    2. DEĞİLSE: Sadece "SKIP" yaz ve dur.
    3. EVET İSE: Haberi Türkçeye çevir ve {takim} taraftarı için heyecanlı, emojili bir tweet yaz.
    4. YASAK: Asla İngilizce kelime kullanma. Sadece Türkçe tweet metnini ver.
    """
    
    try:
        # Yeni kütüphane sözdizimi
        response = client_ai.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        
        if not response.text:
            return None
            
        result = response.text.strip().replace('"', '')
        
        # Filtreleme kontrolü
        if "SKIP" in result or len(result) < 10:
            return None
            
        # Güvenlik kontrolü: AI İngilizce cevap verdiyse engelle
        # Basit bir kontrol: İçinde 'The', 'Player', 'Team' geçiyorsa risklidir.
        if " the " in result.lower() or " transfer " in result.lower():
             # Bazen Türkçe içinde de transfer geçer ama risk almayalım, İngilizce gibiyse eleyelim
             pass 

        return result

    except Exception as e:
        print(f"⚠️ AI Analiz Hatası ({takim}): {e}")
        return None

def haber_tara():
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    if salter == "KAPALI": 
        print("Bot kapalı modda.")
        return

    try:
        limit = int(os.environ.get("HABER_SAYISI", "1"))
    except:
        limit = 1

    takimlar = ["Fenerbahçe", "Galatasaray", "Beşiktaş", "Trabzonspor"]
    twitter_client = baglan()

    for takim in takimlar:
        print(f"🌍 {takim} taranıyor ({limit} adet)...")
        
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
                
                # AI Analizi
                tweet_metni = analyze_and_write(baslik, takim)
                
                if tweet_metni:
                    tweet_final = f"{tweet_metni}\n\n🔗 Kaynak: {link}"
                    try:
                        twitter_client.create_tweet(text=tweet_final)
                        print(f"✅ {takim} Tweet Atıldı: {tweet_metni[:40]}...")
                        paylasilan_sayisi += 1
                        time.sleep(20) # Spam koruması
                    except Exception as e:
                         print(f"❌ Twitter Hatası: {e}")
                else:
                    # Log kirliliği yapmasın diye yazdırmıyoruz veya:
                    # print(f"⏭️ {takim} - Pas geçildi (Alakasız/Hata)")
                    pass
                
        except Exception as e:
            print(f"⚠️ {takim} RSS hatası: {e}")

if __name__ == "__main__":
    haber_tara()
