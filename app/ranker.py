import openai, re, email, os, base64, unicodedata, random
from dotenv import load_dotenv
load_dotenv(); openai.api_key = os.getenv("OPENAI_API_KEY")

def safe_decode(text):
    """Safely decode text and handle special characters"""
    if not text:
        return ""
    try:
        # If it's bytes, decode it
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='ignore')
        # If it's not a string, convert it
        if not isinstance(text, str):
            text = str(text)
        # Remove any problematic characters
        return ''.join(char for char in text if ord(char) < 128)
    except Exception:
        return ""

def get_header_value(headers, name):
    """Safely extract header value"""
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return safe_decode(header.get("value", ""))
    return ""

def sanitize_text(text):
    """Convert Turkish characters to ASCII and remove problematic characters"""
    if not text:
        return ""
    
    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)
    
    # Turkish character mapping
    tr_chars = {
        'ş': 's', 'Ş': 'S',
        'ı': 'i', 'İ': 'I',
        'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U',
        'ö': 'o', 'Ö': 'O',
        'ç': 'c', 'Ç': 'C'
    }
    
    # Replace Turkish characters
    for tr_char, eng_char in tr_chars.items():
        text = text.replace(tr_char, eng_char)
    
    # Remove any remaining non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text

def basic_priority(headers):
    """Determine basic priority from email headers"""
    subject = sanitize_text(headers.get("Subject","")).lower()
    from_addr = sanitize_text(headers.get("From","")).lower()
    
    # VIP senders list - customize this
    vip_domains = ["ceo", "cfo", "cto", "president", "director", "board"]
    
    # Check for VIP sender
    is_vip = any(vip in from_addr for vip in vip_domains)
    
    # Check for urgent keywords in subject
    urgent_keywords = ["urgent", "asap", "emergency", "critical", "immediate", "action required", "deadline"]
    is_urgent = any(keyword in subject for keyword in urgent_keywords)
    
    if is_urgent or is_vip:
        return 1
    return 2

def extract_metadata(message):
    """Extract useful metadata from email"""
    headers = message.get("payload", {}).get("headers", [])
    metadata = {
        "subject": "",
        "from": "",
        "date": "",
        "to": ""
    }
    
    for header in headers:
        name = header.get("name", "").lower()
        if name in metadata:
            value = get_header_value(headers, name)
            metadata[name] = value
            
    return metadata

def truncate_text(text, max_length=2000):
    """Truncate text while keeping complete sentences"""
    text = sanitize_text(text)
    
    if len(text) <= max_length:
        return text
        
    # Find the last complete sentence within max_length
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    
    if last_period > 0:
        return truncated[:last_period + 1] + "\n[... Content truncated ...]"
    return truncated + "\n[... Content truncated ...]"

def get_body(msg):
    """Extract email body safely"""
    try:
        # Get parts or body
        parts = msg.get("payload", {}).get("parts", [])
        
        # If no parts, try getting body directly
        if not parts and "body" in msg.get("payload", {}):
            data = msg["payload"]["body"].get("data", "")
            if data:
                return safe_decode(base64.urlsafe_b64decode(data))
        
        # Try to find text/plain part
        for part in parts:
            if part.get("mimeType") == "text/plain" and "body" in part:
                data = part["body"].get("data", "")
                if data:
                    return safe_decode(base64.urlsafe_b64decode(data))
        
        return "No readable content"
    except Exception as e:
        return f"Error reading email: {str(e)}"

def calculate_priority(subject, sender, body, category):
    """Calculate email priority based on multiple factors"""
    priority = 3  # Default priority

    # Priority keywords in subject
    urgent_keywords = ["urgent", "acil", "immediate", "asap", "emergency", "deadline", "son tarih", "önemli", 
                      "kritik", "hemen", "acilen", "ivedi", "gecikmeyin", "son gün", "son fırsat"]
    important_keywords = ["important", "priority", "attention", "action", "required", "gerekli", "dikkat",
                         "önemli", "öncelikli", "takip", "kontrol", "inceleme", "değerlendirme"]
    
    # VIP sender domains/keywords
    vip_keywords = ["ceo", "cfo", "cto", "director", "manager", "yönetici", "müdür", "direktör", 
                   "founder", "kurucu", "başkan", "genel müdür", "koordinatör", "supervisor"]
    
    # Category-based priority
    high_priority_categories = ["İş", "Kariyer", "Work", "Career", "Job", "Interview", "Mülakat", 
                              "Staj", "Proje", "Görev", "Toplantı", "Eğitim"]
    
    # Check subject for urgent keywords
    if any(keyword in subject.lower() for keyword in urgent_keywords):
        priority -= 2  # Higher priority (lower number)
    elif any(keyword in subject.lower() for keyword in important_keywords):
        priority -= 1

    # Check sender for VIP status
    if any(keyword in sender.lower() for keyword in vip_keywords):
        priority -= 1

    # Check category
    if any(cat.lower() in category.lower() for cat in high_priority_categories):
        priority -= 1

    # Check for deadlines in body
    deadline_keywords = ["deadline", "son tarih", "son gün", "bitiş tarihi", "son başvuru", 
                        "dönüş tarihi", "teslim tarihi", "geç kalma"]
    if any(keyword in body.lower() for keyword in deadline_keywords):
        priority -= 1

    # Ensure priority stays within bounds (1-5)
    return max(1, min(5, priority))

def get_motivation_quote():
    """Return a random motivation quote"""
    quotes = [
        "🌟 'Başarı, her gün küçük adımlar atarak başlar.' - Steve Jobs",
        "💫 'Yapamayacağını düşündüğün şey, seni daha güçlü yapacak olandır.' - Elon Musk",
        "⭐ 'En iyi yatırım, kendinize yapacağınız yatırımdır.' - Warren Buffett",
        "🌠 'Bugün yapabileceğini yarına bırakma.' - Benjamin Franklin",
        "✨ 'Başarı yolculuğunda en önemli adım, başlamaya karar vermektir.' - Walt Disney",
        "🎯 'Hedefleriniz konforlu alanınızın dışında başlar.' - Bill Gates",
        "💪 'Zorluklar, fırsatların kılık değiştirmiş halidir.' - Satya Nadella",
        "🚀 'İmkansız görünen şeyler, sadece henüz başarılmamış olanlardır.' - Mark Zuckerberg",
        "🌈 'Her başarısızlık, başarıya giden yolda bir derstir.' - Thomas Edison",
        "💡 'Yenilik yapmaktan korkmayın, tüm liderler önce yenilikçidir.' - Sundar Pichai"
    ]
    return random.choice(quotes)

def summarize(message):
    """Summarize email content with a beautiful template"""
    try:
        # Get headers
        headers = message.get("payload", {}).get("headers", [])
        
        # Extract metadata
        subject = get_header_value(headers, "subject")
        sender = get_header_value(headers, "from")
        
        # Get and clean body
        body = get_body(message)
        
        # Truncate body if too long (max 1500 chars)
        if len(body) > 1500:
            body = body[:1500] + "..."
            
        # Create prompt
        prompt = f"""Bu e-postayı analiz et ve güzel bir özet oluştur (Türkçe olarak):
📧 Konu: {subject}
👤 Gönderen: {sender}
📝 İçerik: {body}

Lütfen yanıtını tam olarak bu formatta ver:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 ÖNCELİK SEVİYESİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ Öncelik: [1-5] (1=Acil, 5=Düşük)

📋 TEMEL BİLGİLER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Özet: [2-3 satırlık özet]
✅ Yapılması Gereken: [yapılacak işlem veya "İşlem gerekmiyor"]
⏰ Son Tarih: [tarih/saat veya "Son tarih yok"]
🏷️ Kategori: [İş/Kişisel/Bülten/Promosyon]

Emojileri ekle ve formatı koru."""

        # Get completion
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sen bir Türkçe e-posta özetleme asistanısın. Tüm yanıtlarını Türkçe olarak ver."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Extract category from summary
        category = "Genel"
        if "Kategori:" in summary:
            category = summary.split("Kategori:")[1].split("\n")[0].strip()
        
        # Calculate priority based on content
        calculated_priority = calculate_priority(subject, sender, body, category)
        
        # Add motivation quote
        motivation = get_motivation_quote()
        summary += f"\n\n{motivation}"
        
        return summary
        
    except Exception as e:
        # Fallback response with beautiful formatting
        return f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ İŞLEME HATASI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ Öncelik: 3

📋 TEMEL BİLGİLER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Özet: E-posta işlenirken bir hata oluştu
✅ Yapılması Gereken: Orijinal e-postayı kontrol edin
⏰ Son Tarih: Belirtilmemiş
🏷️ Kategori: Sistem Hatası

❌ Hata Detayı: {str(e)}

{get_motivation_quote()}"""

def get_priority_label(priority):
    """Get Turkish priority label"""
    labels = {
        1: "Çok Acil",
        2: "Yüksek Öncelik",
        3: "Normal",
        4: "Düşük Öncelik",
        5: "Bilgi Amaçlı"
    }
    return labels.get(priority, "Normal")
