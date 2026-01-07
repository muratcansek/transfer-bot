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

def ai_translate_and_edit(haber_basligi, takim):
    """Gemini AI haberi Türkçeye çevirir ve bir spor editörü gibi yorumlar."""
    prompt = f"""
    Sen Türkiye'nin en iyi spor editörü ve çevirmenisin. 
    Aşağıdaki haber başlığı yabancı bir dilde (İngilizce vb.) olabilir.
    
    Görevin:
    1. Haberi önce anla ve profesyonel bir Türkçeye çevir.
    2. Çevirdiğin haberi {takim} taraftarları için heyecan verici bir tweet haline getir.
    3. Maksimum 200 karakter kullan.
    4. Spor jargonuna uygun emojiler ekle (🚨, ⏳, ✈️, ✍️ gibi).
    5. Sadece tweet metnini döndür.

    Haber Başlığı: {haber_basligi}
    """
    try:
        response = ai_model.generate_content(prompt)
        return response.text.strip().replace('"', '')
    except Exception as e:
        print(f"AI/Çeviri Hatası: {e}")
        return haber_basligi

def haber_tara():
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    if salter == "KAPALI":
        print("⛔ Bot kapalı modda.")
        return

    # 4 Büyükler
    takimlar = ["Fenerbahçe", "Galatasaray", "Beşiktaş", "Trabzonspor"]
    client = baglan()

    for takim in takimlar:
        print(f"🌍 {takim} için dünya basını (İngilizce kaynaklar) taranıyor...")
        
        # İngilizce transfer haberlerini çekmek için sorguyu güncelledik
        sorgu = urllib.parse.quote(f"{takim} transfer news rumours")
        # Global Google News (İngilizce) kaynağından çekiyoruz
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            root = ElementTree.fromstring(response.content)
            
            # En güncel global haberi al
            item = root.find('./channel/item')
            
            if item is not None:
                baslik = item.find('title').text
                link = item.find('link').text
                
                # Gemini ile Çeviri + Editör Yorumu
                tweet_metni = ai_translate_and_edit(baslik, takim)
                
                tweet_final = f"{tweet_metni}\n\n🔗 Kaynak: {link}"
                
                client.create_tweet(text=tweet_final)
                print(f"✅ {takim} haberi çevrildi ve tweetlendi.")
                
                time.sleep(15) # Twitter sınırı için bekleme
            else:
                print(f"❓ {takim} için dünya basınında yeni haber yok.")
                
        except Exception as e:
            print(f"⚠️ {takim} taranırken hata: {e}")

if __name__ == "__main__":
    haber_tara()
