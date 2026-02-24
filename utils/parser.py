"""
📄 FAYL PARSER
TXT, PDF, DOCX fayllardan savollarni ajratib oladi
Barcha test turlarini qo'llab-quvvatlaydi
"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


# ==================== ASOSIY PARSER ====================

def parse_file(file_path: str) -> List[Dict]:
    """
    Faylni o'qib, savollar ro'yxatini qaytaradi
    Avtomatik test turini aniqlaydi
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
        raise ValueError(f"Qo'llab-quvvatlanmagan format: {extension}")
    
    return parse_text(text)


def parse_text(text: str) -> List[Dict]:
    """
    Matndan savollarni ajratib oladi
    Test turini avtomatik aniqlaydi
    """
    questions = []
    
    # Savollarni bo'lish - raqam. yoki raqam) bilan boshlanadigan
    # Pattern: 1. yoki 1) yoki Q1. yoki SAVOL 1.
    blocks = re.split(
        r'\n(?=\d+[\.\)]\s|Q\d+[\.\)]\s|SAVOL\s*\d+|Savol\s*\d+)',
        text.strip()
    )
    
    for i, block in enumerate(blocks):
        if not block.strip():
            continue
        
        question = _parse_question_block(block.strip(), i + 1)
        if question:
            questions.append(question)
    
    logger.info(f"✅ {len(questions)} ta savol topildi")
    return questions


def _parse_question_block(block: str, number: int) -> Optional[Dict]:
    """Bitta savol blokini parse qilish"""
    lines = [l.strip() for l in block.split('\n') if l.strip()]
    if not lines:
        return None
    
    # Test turini aniqlash
    test_type = _detect_question_type(block)
    
    if test_type == "multiple_choice":
        return _parse_multiple_choice(lines, number)
    elif test_type == "multi_select":
        return _parse_multi_select(lines, number)
    elif test_type == "true_false":
        return _parse_true_false(lines, number)
    elif test_type == "text_input":
        return _parse_text_input(lines, number)
    elif test_type == "matching":
        return _parse_matching(lines, number)
    elif test_type == "ordering":
        return _parse_ordering(lines, number)
    elif test_type == "fill_blank":
        return _parse_fill_blank(lines, number)
    else:
        return _parse_multiple_choice(lines, number)


def _detect_question_type(block: str) -> str:
    """Test turini matn asosida aniqlash"""
    block_lower = block.lower()
    
    # TYPE: tegini tekshirish
    if "type: true_false" in block_lower or "tur: ha/yo'q" in block_lower:
        return "true_false"
    if "type: multi_select" in block_lower or "tur: ko'p_javobli" in block_lower:
        return "multi_select"
    if "type: text_input" in block_lower or "tur: yozma" in block_lower:
        return "text_input"
    if "type: matching" in block_lower or "tur: moslashtirish" in block_lower:
        return "matching"
    if "type: ordering" in block_lower or "tur: tartiblash" in block_lower:
        return "ordering"
    if "type: fill_blank" in block_lower or "tur: to'ldirish" in block_lower:
        return "fill_blank"
    
    # [TO'G'RI] belgisi bilan bir nechta javob
    correct_count = len(re.findall(r'\[TO.G.RI\]|\[CORRECT\]|\[✓\]', block))
    if correct_count > 1:
        return "multi_select"
    
    # Ha/Yo'q tipidagi
    if re.search(r'^\s*[AaАа][)\.]\s*(Ha|Yo.q|True|False|To.g.ri|Noto.g.ri)', block, re.MULTILINE):
        return "true_false"
    
    # Javob: shaklidagi
    if re.search(r'Javob:\s*_+|ANSWER:\s*_+', block):
        return "text_input"
    
    # Default: bir javobli test
    return "multiple_choice"


# ==================== HAR BIR TUR UCHUN PARSER ====================

def _parse_multiple_choice(lines: str, number: int) -> Dict:
    """
    Bir javobli test parser
    Format:
    1. Savol matni
    A) Variant 1
    B) Variant 2 [TO'G'RI]
    C) Variant 3
    D) Variant 4
    Izoh: Bu variant to'g'ri chunki...
    """
    question_text = ""
    options = []
    correct_index = 0
    explanation = ""
    score = 1
    
    i = 0
    # Savol matnini olish
    question_line = lines[0]
    # Raqam va nuqtani olib tashlash
    question_text = re.sub(r'^\d+[\.\)]\s*', '', question_line).strip()
    
    # Variantlarni olish
    option_pattern = re.compile(r'^([A-Da-dАаBbВвСсDd])[\.)\s]\s*(.+)', re.UNICODE)
    
    for line in lines[1:]:
        if line.lower().startswith(('izoh:', 'explanation:', 'tushuntirish:', 'note:')):
            explanation = re.sub(r'^(izoh|explanation|tushuntirish|note):\s*', '', line, flags=re.IGNORECASE)
            continue
        
        if line.lower().startswith(('ball:', 'score:', 'bahо:')):
            try:
                score = int(re.search(r'\d+', line).group())
            except:
                pass
            continue
        
        match = option_pattern.match(line)
        if match:
            option_text = match.group(2).strip()
            is_correct = bool(re.search(r'\[TO.G.RI\]|\[CORRECT\]|\[✓\]|\*$', option_text, re.IGNORECASE))
            # To'g'ri belgini olib tashlash
            option_text = re.sub(r'\s*\[TO.G.RI\]|\s*\[CORRECT\]|\s*\[✓\]|\s*\*$', '', option_text, flags=re.IGNORECASE).strip()
            
            if is_correct:
                correct_index = len(options)
            
            options.append(option_text)
    
    if not question_text or not options:
        return None
    
    return {
        "number": number,
        "type": "multiple_choice",
        "question": question_text,
        "options": options,
        "correct_answer": correct_index,
        "explanation": explanation,
        "score": score,
        "image_url": None,
        "video_url": None
    }


def _parse_multi_select(lines: list, number: int) -> Dict:
    """
    Ko'p javobli test parser
    Format:
    2. Quyidagilardan qaysilari to'g'ri?
    TYPE: MULTI_SELECT
    A) Variant 1 [TO'G'RI]
    B) Variant 2
    C) Variant 3 [TO'G'RI]
    D) Variant 4
    """
    question_text = re.sub(r'^\d+[\.\)]\s*', '', lines[0]).strip()
    options = []
    correct_indexes = []
    explanation = ""
    score = 1
    
    option_pattern = re.compile(r'^([A-Da-d])[\.)\s]\s*(.+)', re.UNICODE)
    
    for line in lines[1:]:
        if 'type:' in line.lower() or 'tur:' in line.lower():
            continue
        if line.lower().startswith(('izoh:', 'explanation:')):
            explanation = re.sub(r'^(izoh|explanation):\s*', '', line, flags=re.IGNORECASE)
            continue
        
        match = option_pattern.match(line)
        if match:
            option_text = match.group(2).strip()
            is_correct = bool(re.search(r'\[TO.G.RI\]|\[CORRECT\]|\[✓\]', option_text, re.IGNORECASE))
            option_text = re.sub(r'\s*\[TO.G.RI\]|\s*\[CORRECT\]|\s*\[✓\]', '', option_text, flags=re.IGNORECASE).strip()
            
            if is_correct:
                correct_indexes.append(len(options))
            options.append(option_text)
    
    return {
        "number": number,
        "type": "multi_select",
        "question": question_text,
        "options": options,
        "correct_answers": correct_indexes,
        "explanation": explanation,
        "score": len(correct_indexes),
        "image_url": None,
        "video_url": None
    }


def _parse_true_false(lines: list, number: int) -> Dict:
    """
    Ha/Yo'q test parser
    Format:
    3. Er yuzining 70% suv bilan qoplangan.
    TYPE: TRUE_FALSE
    Javob: Ha
    Izoh: To'g'ri, er yuzining 71% suv.
    """
    question_text = re.sub(r'^\d+[\.\)]\s*', '', lines[0]).strip()
    correct_answer = True
    explanation = ""
    
    for line in lines[1:]:
        line_lower = line.lower()
        if 'javob:' in line_lower or 'answer:' in line_lower or 'to\'g\'ri javob:' in line_lower:
            answer_text = re.sub(r'(javob|answer|to.g.ri javob):\s*', '', line, flags=re.IGNORECASE).strip().lower()
            correct_answer = answer_text in ['ha', 'to\'g\'ri', 'true', 'yes', '1', '+']
        elif line.lower().startswith(('izoh:', 'explanation:')):
            explanation = re.sub(r'^(izoh|explanation):\s*', '', line, flags=re.IGNORECASE)
    
    return {
        "number": number,
        "type": "true_false",
        "question": question_text,
        "options": ["✅ Ha (To'g'ri)", "❌ Yo'q (Noto'g'ri)"],
        "correct_answer": 0 if correct_answer else 1,
        "explanation": explanation,
        "score": 1,
        "image_url": None,
        "video_url": None
    }


def _parse_text_input(lines: list, number: int) -> Dict:
    """
    Yozma javob test parser
    Format:
    4. Python kimlar tomonidan yaratilgan?
    TYPE: TEXT_INPUT
    Javob: Guido van Rossum
    Qabul_qilinadigan: guido,guido van rossum,rossum
    Izoh: Python 1991-yilda yaratilgan.
    """
    question_text = re.sub(r'^\d+[\.\)]\s*', '', lines[0]).strip()
    correct_answer = ""
    acceptable = []
    explanation = ""
    
    for line in lines[1:]:
        line_lower = line.lower()
        if 'javob:' in line_lower or 'answer:' in line_lower:
            correct_answer = re.sub(r'(javob|answer):\s*', '', line, flags=re.IGNORECASE).strip()
            acceptable = [correct_answer.lower()]
        elif 'qabul_qilinadigan:' in line_lower or 'acceptable:' in line_lower:
            vals = re.sub(r'(qabul_qilinadigan|acceptable):\s*', '', line, flags=re.IGNORECASE)
            acceptable = [v.strip().lower() for v in vals.split(',')]
        elif line.lower().startswith(('izoh:', 'explanation:')):
            explanation = re.sub(r'^(izoh|explanation):\s*', '', line, flags=re.IGNORECASE)
    
    return {
        "number": number,
        "type": "text_input",
        "question": question_text,
        "correct_answer": correct_answer,
        "acceptable_answers": acceptable,
        "explanation": explanation,
        "score": 2,
        "image_url": None,
        "video_url": None
    }


def _parse_matching(lines: list, number: int) -> Dict:
    """
    Moslashtirish test parser
    Format:
    5. Mamlakat va poytaxtlarni moslang:
    TYPE: MATCHING
    CHAP: O'zbekiston | Toshkent
    CHAP: Rossiya | Moskva
    CHAP: Fransiya | Parij
    CHAP: Yaponiya | Tokiyo
    """
    question_text = re.sub(r'^\d+[\.\)]\s*', '', lines[0]).strip()
    left_items = []
    right_items = []
    correct_pairs = {}
    explanation = ""
    
    for line in lines[1:]:
        if 'type:' in line.lower() or 'tur:' in line.lower():
            continue
        if line.upper().startswith('CHAP:') or line.upper().startswith('LEFT:'):
            parts = re.sub(r'^(chap|left):\s*', '', line, flags=re.IGNORECASE).split('|')
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                idx = len(left_items)
                left_items.append(left)
                right_items.append(right)
                correct_pairs[idx] = idx
        elif line.lower().startswith(('izoh:', 'explanation:')):
            explanation = re.sub(r'^(izoh|explanation):\s*', '', line, flags=re.IGNORECASE)
    
    return {
        "number": number,
        "type": "matching",
        "question": question_text,
        "left_items": left_items,
        "right_items": right_items,
        "correct_pairs": correct_pairs,
        "explanation": explanation,
        "score": len(left_items),
        "image_url": None,
        "video_url": None
    }


def _parse_ordering(lines: list, number: int) -> Dict:
    """
    Tartiblash test parser
    Format:
    6. Quyidagi bosqichlarni to'g'ri tartibda joylashtiring:
    TYPE: ORDERING
    1. Muammoni aniqlash
    2. Ma'lumot to'plash
    3. Yechim topish
    4. Natijani tekshirish
    """
    question_text = re.sub(r'^\d+[\.\)]\s*', '', lines[0]).strip()
    items = []
    explanation = ""
    
    item_pattern = re.compile(r'^\d+[\.\)]\s*(.+)')
    
    for line in lines[1:]:
        if 'type:' in line.lower() or 'tur:' in line.lower():
            continue
        if line.lower().startswith(('izoh:', 'explanation:')):
            explanation = re.sub(r'^(izoh|explanation):\s*', '', line, flags=re.IGNORECASE)
            continue
        match = item_pattern.match(line)
        if match:
            items.append(match.group(1).strip())
    
    correct_order = list(range(len(items)))
    
    return {
        "number": number,
        "type": "ordering",
        "question": question_text,
        "items": items,
        "correct_order": correct_order,
        "explanation": explanation,
        "score": len(items),
        "image_url": None,
        "video_url": None
    }


def _parse_fill_blank(lines: list, number: int) -> Dict:
    """
    Bo'sh joyni to'ldirish parser
    Format:
    7. Python dasturlash tili ___ yilda yaratilgan.
    TYPE: FILL_BLANK
    Javob: 1991
    Izoh: Python 1991-yilda Guido van Rossum tomonidan yaratilgan.
    """
    question_text = re.sub(r'^\d+[\.\)]\s*', '', lines[0]).strip()
    correct_answer = ""
    explanation = ""
    
    for line in lines[1:]:
        if 'javob:' in line.lower() or 'answer:' in line.lower():
            correct_answer = re.sub(r'(javob|answer):\s*', '', line, flags=re.IGNORECASE).strip()
        elif line.lower().startswith(('izoh:', 'explanation:')):
            explanation = re.sub(r'^(izoh|explanation):\s*', '', line, flags=re.IGNORECASE)
    
    return {
        "number": number,
        "type": "fill_blank",
        "question": question_text,
        "correct_answer": correct_answer,
        "acceptable_answers": [correct_answer.lower()],
        "explanation": explanation,
        "score": 1,
        "image_url": None,
        "video_url": None
    }


# ==================== FAYL O'QISH FUNKSIYALARI ====================

def _read_txt(file_path: str) -> str:
    """TXT faylni o'qish"""
    encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError("Fayl kodlanishini aniqlab bo'lmadi")


def _read_pdf(file_path: str) -> str:
    """PDF faylni o'qish"""
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
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise ImportError("PDF o'qish uchun: pip install pdfplumber")


def _read_docx(file_path: str) -> str:
    """DOCX faylni o'qish"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except ImportError:
        raise ImportError("DOCX o'qish uchun: pip install python-docx")
