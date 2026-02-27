"""
📄 FAYL PARSER (PRO VERSIYA)
Endi to'g'ri javoblarni belgilash uchun shunchaki * (yulduzcha), === yoki [TO'G'RI] ishlatsangiz ham bo'ladi.
Barcha 7 turdagi test namunalarini muammosiz o'qiydi!
"""
import re
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

def _read_txt(file_path: str) -> str:
    encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError("Fayl kodlanishini aniqlab bo'lmadi. Iltimos, UTF-8 formatida saqlang.")

def _read_pdf(file_path: str) -> str:
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
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except ImportError:
        raise ImportError("DOCX o'qish uchun kutubxona yetishmayapti: pip install python-docx")


def parse_file(file_path: str) -> List[Dict]:
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
    questions = []
    text = text.replace('\r\n', '\n')
    text = "\n" + text.strip()
    blocks = re.split(r'\n(?=\d+[\.\)])', text)
    
    for block in blocks:
        block = block.strip()
        if not block: continue
            
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines: continue
            
        raw_question = lines[0]
        question_text = re.sub(r'^\d+[\.\)]\s*', '', raw_question)
        
        q_data = {
            "type": "multiple_choice",
            "question": question_text,
            "options": [],
            "correct": None,
            "explanation": "Izoh kiritilmagan.",
            "points": 1,
            "accepted_answers": []
        }
        
        for line in lines:
            upper_line = line.upper()
            if upper_line.startswith("TYPE:"):
                q_data["type"] = line[5:].strip().lower()
            elif upper_line.startswith("IZOH:"):
                q_data["explanation"] = line[5:].strip()
            elif upper_line.startswith("BALL:"):
                try: q_data["points"] = int(re.findall(r'\d+', line)[0])
                except: pass

        # 🔘 TUR 1: BIR JAVOBLI (Yulduzchani va === ni taniydi)
        if q_data["type"] == "multiple_choice":
            for line in lines[1:]:
                # === va * belgilari tozalangach A, B harflari qolishini tekshiramiz
                clean_line_for_check = line.replace('*', '').replace('=', '').strip()
                if re.search(r'^[A-Za-z][\.\)]', clean_line_for_check):
                    is_correct = "[TO'G'RI]" in line.upper() or "*" in line or "===" in line
                    clean_opt = re.sub(r'\[TO\'G\'RI\]', '', line, flags=re.IGNORECASE).replace('*', '').replace('=', '').strip()
                    q_data["options"].append(clean_opt)
                    if is_correct and not q_data["correct"]:
                        q_data["correct"] = clean_opt
            
            # Agar variantlar topsa, lekin belgilash (===) esdan chiqqan bo'lsa, xato bermay 1-javobni oladi
            if q_data["options"] and not q_data["correct"]:
                q_data["correct"] = q_data["options"][0]

        # ☑️ TUR 2: KO'P JAVOBLI (Yulduzchani va === ni taniydi)
        elif q_data["type"] == "multi_select":
            q_data["correct"] = []
            for line in lines[1:]:
                clean_line_for_check = line.replace('*', '').replace('=', '').strip()
                if re.search(r'^[A-Za-z][\.\)]', clean_line_for_check):
                    is_correct = "[TO'G'RI]" in line.upper() or "*" in line or "===" in line
                    clean_opt = re.sub(r'\[TO\'G\'RI\]', '', line, flags=re.IGNORECASE).replace('*', '').replace('=', '').strip()
                    q_data["options"].append(clean_opt)
                    if is_correct:
                        q_data["correct"].append(clean_opt)
            
            if q_data["options"] and not q_data["correct"]:
                q_data["correct"].append(q_data["options"][0])

        elif q_data["type"] == "true_false":
            q_data["options"] = ["✅ Ha", "❌ Yo'q"]
            for line in lines[1:]:
                if line.upper().startswith("JAVOB:"):
                    ans = line[6:].strip().lower()
                    if ans in ["ha", "true", "yes", "to'g'ri"]: q_data["correct"] = "✅ Ha"
                    else: q_data["correct"] = "❌ Yo'q"

        elif q_data["type"] in ["text_input", "fill_blank"]:
            for line in lines[1:]:
                if line.upper().startswith("JAVOB:"):
                    q_data["correct"] = line[6:].strip()
                elif line.upper().startswith("QABUL_QILINADIGAN:"):
                    acc_str = line[18:].strip()
                    q_data["accepted_answers"] = [x.strip().lower() for x in acc_str.split(",")]

        elif q_data["type"] == "matching":
            q_data["correct"] = {}
            for line in lines[1:]:
                if line.upper().startswith("CHAP:"):
                    parts = line[5:].split("|")
                    if len(parts) == 2:
                        q_data["correct"][parts[0].strip()] = parts[1].strip()

        elif q_data["type"] == "ordering":
            q_data["correct"] = []
            for line in lines[1:]:
                if re.match(r'^\d+[\.\)]', line) and not line.upper().startswith("TYPE:"):
                    q_data["correct"].append(line.strip())

        # Agar to'g'ri javob topilgan bo'lsa yoki matn kiritish turi bo'lsa, savolni bazaga yozamiz
        if q_data["correct"] or q_data["type"] in ["text_input", "fill_blank"]:
            questions.append(q_data)
            
    return questions
