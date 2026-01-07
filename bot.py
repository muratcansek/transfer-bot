import tweepy
import os
import requests
import time
from xml.etree import ElementTree
import urllib.parse
from google import genai

# --- AI YAPILANDIRMASI ---
# Gemini API anahtarının GitHub Secrets'ta 'GEMINI_API_KEY' adıyla kayıtlı olduğundan emin ol.
client_ai = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def baglan():
    return tweepy.Client(
        consumer_key=os.environ.get("TWITTER_API_KEY"),
        consumer_secret=os.environ.get("TWITTER_API_SECRET"),
        access_token=os.environ.get("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
    )

def ai_editor_yorumu(haber_basligi, takim):
    """Yabancı haberi Türkçeye çevirir, özetler ve editör gibi yorumlar."""
    # Gemini'ye verdiğimiz komutu çok daha sert ve net hale getirdik.
    prompt = f"""
    Sen profesyonel bir spor editörüsün. Sana gelen haber başlığı İngilizce veya başka bir dildedir.
    
    Görevin:
    1. Haberi önce Türkçeye çevir ve en önemli kısmını özetle.
    2. {takim} taraftarlarını heyecanlandıracak bir spor haberi formatında yeniden yaz.
    3. Metin kesinlikle Türkçe olmalı. İngilizce kelime bırakma.
    4. Maksimum 200 karakter ve etkileyici emojiler kullan.
    5. Kaynak linkini ben ekleyeceğim, sen sadece tweet metnini yaz.
    6. "Dedi", "Açıklandı" gibi resmi diller yerine "Flaş gelişme!", "Bombalar patlıyor!" gibi editör jargonu kullan.

    Haber Başlığı: {haber_basligi}
    """
    try:
        response = client_ai.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        # AI'dan gelen cevabın boş veya hatalı olup olmadığını kontrol ediyoruz
        result = response.text.strip().replace('"', '')
        if not result or len(result) < 5:
            return f"🚨 {takim.upper()} SICAK GELİŞME: {haber_basligi}"
        return result
    except Exception as e:
        print(f"AI İşlem Hatası: {e}")
        # Eğer AI hata verirse, en azından manuel bir Türkçe format üretelim
        return f"🚨 {takim} Transfer Gelişmesi: {haber_basligi}"

def haber_tara():
    salter = os.environ.get("BOT_DURUMU", "ACIK").upper()
    if salter == "KAPALI":
        return

    takimlar = ["Fenerbahçe", "Galatasaray", "Beşiktaş", "Trabzonspor"]
    twitter_client = baglan()

    for takim in takimlar:
        print(f"🌍 {takim} için global tarama başladı...")
        
        # İngilizce (Global) haberleri çekmek için sorgu
        sorgu = urllib.parse.quote(f"{takim} transfer news rumours")
        url = f"https://news.google.com/rss/search?q={sorgu}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            root = ElementTree.fromstring(response.content)
            item = root.find('./channel/item')
            
            if item is not None:
                baslik = item.find('title').text
                link = item.find('link').text
                
                # Gemini Editör/Çeviri Süreci
                tweet_metni = ai_editor_yorumu(baslik, takim)
                
                # Final Tweet: Editör yorumu + Altına kaynak linki
                tweet_final = f"{tweet_metni}\n\n🔗 Kaynak: {link}"
                
                twitter_client.create_tweet(text=tweet_final)
                print(f"✅ {takim} haberi başarıyla paylaşıldı.")
                
                time.sleep(20) # Twitter API sağlığı için bekleme
            else:
                print(f"❓ {takim} için yeni bir haber bulunamadı.")
                
        except Exception as e:
            print(f"⚠️ {takim} hatası: {e}")

if __name__ == "__main__":
    haber_tara()
