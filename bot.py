import telebot
import re
import pandas as pd
from fpdf import FPDF
import os

BOT_TOKEN = '8722810868:AAE22aXbMwPySAj6cwiBUKWsHKN6h3r08y4'
bot = telebot.TeleBot(BOT_TOKEN)

def parse_measurements(text):
    kamber_match = re.search(r'(?:كراين|kamber|camber|no)\s*[:.-]?\s*(\d+)', text, re.IGNORECASE)
    kamber_no = kamber_match.group(1) if kamber_match else "Belirtilmedi"

    lines = text.strip().split('\n')
    data = []
    total_sqm = 0

    for line in lines:
        matches = re.findall(r'(\d{3,4})\s*[xX*\/]\s*(\d{3,4})', line)
        for w, h in matches:
            en = int(w)
            boy = int(h)
            adet = 1
            m2 = (en * boy) / 1000000.0
            total_sqm += m2

            data.append({
                "Kamber / كراين": kamber_no,
                "En (mm)": en,
                "Boy (mm)": boy,
                "Adet": adet,
                "Alan (m2)": round(m2, 3)
            })

    return data, kamber_no, total_sqm

def create_pdf(df, kamber_no, total_sqm, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(100, 10, "Cam Uretim & Firin Giris Raporu", 0, 0, 'L')
    pdf.cell(90, 10, f"Kamber / Karayn: {kamber_no}", 0, 1, 'R')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    cols = ["En (mm)", "Boy (mm)", "Adet", "Alan (m2)"]
    for col in cols:
        pdf.cell(45, 10, col, 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font("Arial", "", 12)
    for _, row in df.iterrows():
        pdf.cell(45, 10, str(row["En (mm)"]), 1, 0, 'C')
        pdf.cell(45, 10, str(row["Boy (mm)"]), 1, 0, 'C')
        pdf.cell(45, 10, str(row["Adet"]), 1, 0, 'C')
        pdf.cell(45, 10, str(row["Alan (m2)"]), 1, 0, 'C')
        pdf.ln()
        
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"Toplam Alan: {round(total_sqm, 3)} m2", 0, 1, 'R')
    pdf.output(filename)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Cam Fırın Takip Botu Hazır!\nÖlçüleri metin olarak gönderebilirsiniz.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text
    data, kamber_no, total_sqm = parse_measurements(text)
    
    if not data:
        bot.reply_to(message, "Ölçü bulunamadı. Örnek format:\nكراين: 5\n950x2100\n1200x1500")
        return
        
    df = pd.DataFrame(data)
    excel_file = f"Uretim_{kamber_no}.xlsx"
    pdf_file = f"Uretim_{kamber_no}.pdf"
    
    df.to_excel(excel_file, index=False)
    create_pdf(df, kamber_no, total_sqm, pdf_file)
    
    ozet = (
        f"✅ **Rapor Hazırlandı**\n\n"
        f"📌 **كراين / Kamber No:** {kamber_no}\n"
        f"📦 **Toplam Parça:** {len(data)} Adet (Tekil)\n"
        f"📐 **Toplam Alan:** {round(total_sqm, 3)} m²"
    )
    bot.send_message(message.chat.id, ozet, parse_mode="Markdown")
    
    with open(excel_file, 'rb') as doc:
        bot.send_document(message.chat.id, doc)
    with open(pdf_file, 'rb') as doc:
        bot.send_document(message.chat.id, doc)
        
    if os.path.exists(excel_file): os.remove(excel_file)
    if os.path.exists(pdf_file): os.remove(pdf_file)

print("Bot calisiyor...")
bot.infinity_polling()
