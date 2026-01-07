import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai

# --- YENİ GEMINI YAPILANDIRMASI ---
client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def ai_translate_and_edit(haber_basligi, takim):
    """Yabancı haberleri Türkçeye çevirir ve bir editör gibi yorumlar."""
    prompt = f"""
    Sen profesyonel bir Türk spor editörü ve çevirmenisin.
    Aşağıdaki haber başlığı yabancı bir dilde (İngilizce vb.) olabilir.
    
    Talimatlar:
    1. Haberi önce doğru bir Türkçeye çevir.
    2. Çevirdiğin haberi {takim} taraftarlarını heyecanlandıracak şekilde yorumla.
    3. Maksimum 220 karakterlik, bol etkileşim alacak bir tweet haline getir.
    4. Spor jargonuna uygun emojiler kullan.
    5. Sadece tweet metnini döndür.

    Haber Başlığı: {haber_basligi}
    """
    try:
        # Google-genai'nin en güncel metin üretim komutu
        response = client_ai.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text.strip().replace('"', '')
    except Exception as e:
        print(f"AI İşlem Hatası: {e}")
        return haber_basligi

def haber_tara():
    # Şalter Kontrolü
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    if salter == "KAPALI":
        print("⛔ Şalter Kapalı: Bot uyku modunda.")
        return

    takimlar = ["Fenerbahçe", "Galatasaray", "Beşiktaş", "Trabzonspor"]
    twitter_client = baglan()

    for takim in takimlar:
        print(f"🌍 {takim} için dünya basını taranıyor...")
        
        # Global Google News üzerinden İngilizce aramalar (Sorgu: Takım + transfer haberleri)
        sorgu = urllib.parse.quote(f"{takim} transfer news rumours")
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            root = ElementTree.fromstring(response.content)
            
            # Kaynaktaki ilk (en yeni) haberi al
            item = root.find('./channel/item')
            
            if item is not None:
                baslik = item.find('title').text
                link = item.find('link').text
                
                # AI hem çeviri yapar hem editör dokunuşu ekler
                tweet_metni = ai_translate_and_edit(baslik, takim)
                
                # Tweeti Oluştur ve Gönder
                tweet_final = f"{tweet_metni}\n\n🔗 Detay: {link}"
                twitter_client.create_tweet(text=tweet_final)
                
                print(f"✅ {takim} tweeti başarıyla atıldı.")
                
                # Twitter sınırlarına takılmamak için 15 saniye bekle
                time.sleep(15)
            else:
                print(f"❓ {takim} için güncel bir haber bulunamadı.")
                
        except Exception as e:
            print(f"⚠️ {takim} taranırken bir aksaklık oldu: {e}")

if __name__ == "__main__":
    haber_tara()
