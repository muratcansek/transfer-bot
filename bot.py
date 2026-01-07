import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
import google.generativeai as genai

# --- YAPILANDIRMA ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def ai_editor_yorumu(haber_basligi, takim):
    """Gemini AI haberi okur ve bir spor editörü gibi yorumlar."""
    prompt = f"""
    Sen Türkiye'nin en popüler spor editörlerinden birisin. 
    Aşağıda gelen haber başlığını oku ve {takim} taraftarlarını heyecanlandıracak, 
    merak uyandırıcı ve profesyonel bir tweet haline getir. 
    
    Kurallar:
    1. Maksimum 200 karakter olsun.
    2. Futbol jargonuna uygun emojiler kullan.
    3. Haberin özünü bozma ama daha çarpıcı yaz.
    4. Sadece tweet metnini döndür, açıklama yapma.

    Haber Başlığı: {haber_basligi}
    """
    try:
        response = ai_model.generate_content(prompt)
        return response.text.strip().replace('"', '')
    except Exception as e:
        print(f"AI Hatası: {e}")
        return haber_basligi # Hata olursa orijinal başlığı kullan

def haber_tara():
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    if salter == "KAPALI":
        print("⛔ Bot kapalı modda.")
        return

    takimlar = ["Fenerbahçe", "Galatasaray", "Beşiktaş", "Trabzonspor"]
    client = baglan()

    for takim in takimlar:
        print(f"🔄 {takim} için dünya basını taranıyor...")
        
        # Google News sorgusu: Hem yerel hem global haberleri yakalamak için
        sorgu = urllib.parse.quote(f"{takim} transfer news")
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=tr&gl=TR&ceid=TR:tr"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            root = ElementTree.fromstring(response.content)
            
            # En güncel haberi alıyoruz
            item = root.find('./channel/item')
            
            if item is not None:
                baslik = item.find('title').text
                link = item.find('link').text
                
                # AI Editör yorumunu al
                tweet_metni = ai_editor_yorumu(baslik, takim)
                
                # Final Tweet: AI Yorumu + Link
                tweet_final = f"{tweet_metni}\n\n🔗 Kaynak: {link}"
                
                client.create_tweet(text=tweet_final)
                print(f"✅ {takim} tweeti atıldı.")
                
                # Twitter'ın spam filtresine takılmamak için bekle
                time.sleep(15)
            else:
                print(f"❓ {takim} için yeni haber bulunamadı.")
                
        except Exception as e:
            print(f"⚠️ {takim} taranırken hata: {e}")

if __name__ == "__main__":
    haber_tara()
