"""
📄 FAYL PARSER (PRO VERSIYA)
TXT, PDF, DOCX fayllardan 7 xil turdagi savollarni xatosiz ajratib oluvchi aqlli modul.
Hech qanday qisqartirishlarsiz, barcha qoidalar qo'llab-quvvatlanadi.
"""
import re
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

# ==========================================================
# 1. FAYLLARNI O'QISH (I/O) OPERATSIYALARI
# ==========================================================

def _read_txt(file_path: str) -> str:
    """TXT faylni xavfsiz o'qish (Turli kodirovkalarni tekshiradi)"""
    encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError("Fayl kodlanishini aniqlab bo'lmadi. Iltimos, UTF-8 formatida saqlang.")

def _read_pdf(file_path: str) -> str:
    """PDF fayldan matnni ajratib olish"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except ImportError:
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    if page.extract_text():
                        text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise ImportError("PDF o'qish uchun kutubxona yetishmayapti: pip install pdfplumber PyPDF2")

def _read_docx(file_path: str) -> str:
    """Word (DOCX) faylidan matnni o'qish"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except ImportError:
        raise ImportError("DOCX o'qish uchun kutubxona yetishmayapti: pip install python-docx")


# ==========================================================
# 2. ASOSIY PARSER FUNKSIYALARI
# ==========================================================

def parse_file(file_path: str) -> List[Dict]:
    """
    Fayl turini aniqlab, tegishli o'quvchini ishga tushiradi
    va matnni tahlil qilib savollar ro'yxatini qaytaradi.
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    
    if extension == ".txt":
        text = _read_txt(file_path)
    elif extension == ".pdf":
        text = _read_pdf(file_path)
    elif extension in [".docx", ".doc"]:
        text = _read_docx(file_path)
    else:
        raise ValueError(f"❌ Qo'llab-quvvatlanmagan fayl formati: {extension}")
    
    return parse_text(text)


def parse_text(text: str) -> List[Dict]:
    """
    Katta matnni 7 xil test turlariga ajratuvchi va ularni 
    to'g'ri JSON (Dict) formatiga soluvchi AI-simon mantiq.
    """
    questions = []
    
    # Matnni tozalash va birxillashtirish
    text = text.replace('\r\n', '\n')
    text = "\n" + text.strip()
    
    # Savollarni raqamiga qarab bo'laklarga ajratish (Masalan: "1. ", "12) ")
    blocks = re.split(r'\n(?=\d+[\.\)])', text)
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines:
            continue
            
        # 1. Savol matnini tozalab olish (Raqamni olib tashlash)
        raw_question = lines[0]
        question_text = re.sub(r'^\d+[\.\)]\s*', '', raw_question)
        
        q_data = {
            "type": "multiple_choice", # Standart tur
            "question": question_text,
            "options": [],
            "correct": None,
            "explanation": "Izoh kiritilmagan.",
            "points": 1,
            "accepted_answers": []
        }
        
        # 2. Xususiyatlarni qidirish (TYPE, Izoh, Ball)
        for line in lines:
            upper_line = line.upper()
            if upper_line.startswith("TYPE:"):
                q_data["type"] = line[5:].strip().lower()
            elif upper_line.startswith("IZOH:"):
                q_data["explanation"] = line[5:].strip()
            elif upper_line.startswith("BALL:"):
                try:
                    q_data["points"] = int(re.findall(r'\d+', line)[0])
                except: pass

        # 3. TEST TURIGA QARAB JAVOBLARNI AJRATISH MANTIQI
        
        # 🔘 TUR 1: BIR JAVOBLI (Multiple Choice)
        if q_data["type"] == "multiple_choice":
            for line in lines[1:]:
                if re.match(r'^[A-Za-z][\.\)]', line):
                    is_correct = "[TO'G'RI]" in line.upper()
                    clean_opt = re.sub(r'\[TO\'G\'RI\]', '', line, flags=re.IGNORECASE).strip()
                    q_data["options"].append(clean_opt)
                    if is_correct:
                        q_data["correct"] = clean_opt

        # ☑️ TUR 2: KO'P JAVOBLI (Multi Select)
        elif q_data["type"] == "multi_select":
            q_data["correct"] = []
            for line in lines[1:]:
                if re.match(r'^[A-Za-z][\.\)]', line):
                    is_correct = "[TO'G'RI]" in line.upper()
                    clean_opt = re.sub(r'\[TO\'G\'RI\]', '', line, flags=re.IGNORECASE).strip()
                    q_data["options"].append(clean_opt)
                    if is_correct:
                        q_data["correct"].append(clean_opt)

        # ✅ TUR 3: HA YOKI YO'Q (True/False)
        elif q_data["type"] == "true_false":
            q_data["options"] = ["✅ Ha", "❌ Yo'q"]
            for line in lines[1:]:
                if line.upper().startswith("JAVOB:"):
                    ans = line[6:].strip().lower()
                    if ans in ["ha", "true", "yes", "to'g'ri"]:
                        q_data["correct"] = "✅ Ha"
                    else:
                        q_data["correct"] = "❌ Yo'q"

        # ✍️ TUR 4 & 5: YOZMA JAVOB VA BO'SH JOY (Text Input & Fill Blank)
        elif q_data["type"] in ["text_input", "fill_blank"]:
            for line in lines[1:]:
                if line.upper().startswith("JAVOB:"):
                    q_data["correct"] = line[6:].strip()
                elif line.upper().startswith("QABUL_QILINADIGAN:"):
                    acc_str = line[18:].strip()
                    # Vergul bilan ajratilgan javoblarni tozalab ro'yxatga olamiz
                    q_data["accepted_answers"] = [x.strip().lower() for x in acc_str.split(",")]

        # 🔗 TUR 6: MOSLASHTIRISH (Matching)
        elif q_data["type"] == "matching":
            q_data["correct"] = {}
            for line in lines[1:]:
                if line.upper().startswith("CHAP:"):
                    parts = line[5:].split("|")
                    if len(parts) == 2:
                        q_data["correct"][parts[0].strip()] = parts[1].strip()

        # 🔢 TUR 7: TARTIBLASH (Ordering)
        elif q_data["type"] == "ordering":
            q_data["correct"] = []
            for line in lines[1:]:
                # "1. Nimadir" formatini ushlab olish
                if re.match(r'^\d+[\.\)]', line) and not line.upper().startswith("TYPE:"):
                    q_data["correct"].append(line.strip())

        # 4. Yaroqliligini tekshirish va ro'yxatga qo'shish
        # Agar to'g'ri javob topilgan bo'lsa yoki yozma test bo'lsa uni qabul qilamiz
        if q_data["correct"] or q_data["type"] in ["text_input", "fill_blank"]:
            questions.append(q_data)
            
    return questions
