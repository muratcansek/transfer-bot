import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai

client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def ai_editor_yorumu(haber_basligi, takim):
    prompt = f"Sen profesyonel bir Türk spor editörüsün. Şu yabancı haberi Türkçeye çevir ve {takim} taraftarları için etkileyici, kısa bir tweet yaz: {haber_basligi}"
    try:
        response = client_ai.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        return response.text.strip().replace('"', '')
    except:
        return f"🚨 {takim} Gelişmesi: {haber_basligi}"

def haber_tara():
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    if salter == "KAPALI": return

    # Kutucuğa yazılan sayıyı alıyoruz (Hata olmasın diye sayıya çeviriyoruz)
    try:
        limit = int(os.environ.get("HABER_SAYISI", "1"))
    except:
        limit = 1

    takimlar = ["Fenerbahçe", "Galatasaray", "Beşiktaş", "Trabzonspor"]
    twitter_client = baglan()

    for takim in takimlar:
        print(f"🌍 {takim} için {limit} adet haber aranıyor...")
        sorgu = urllib.parse.quote(f"{takim} transfer news rumours")
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            root = ElementTree.fromstring(response.content)
            
            # Kaynaktaki haberleri senin seçtiğin limit kadar alıyoruz
            haberler = root.findall('./channel/item')[:limit]
            
            for item in haberler:
                baslik = item.find('title').text
                link = item.find('link').text
                
                tweet_metni = ai_editor_yorumu(baslik, takim)
                tweet_final = f"{tweet_metni}\n\n🔗 Kaynak: {link}"
                
                twitter_client.create_tweet(text=tweet_final)
                print(f"✅ {takim} için bir haber paylaşıldı.")
                time.sleep(15) # Twitter koruması
                
        except Exception as e:
            print(f"⚠️ {takim} hatası: {e}")

if __name__ == "__main__":
    haber_tara()
