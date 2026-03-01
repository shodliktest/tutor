"""
📄 FAYL PARSER — TXT / PDF / DOCX
To'g'ri javob belgilash: ===, * (yulduzcha), [TO'G'RI]
7 xil test turini tushunadi
"""
import re
import logging
from pathlib import Path
from typing import List, Dict

log = logging.getLogger(__name__)


def parse_file(path: str) -> List[Dict]:
    """Faylni o'qib, savollar ro'yxatini qaytaradi"""
    ext = Path(path).suffix.lower()
    try:
        if ext == ".txt":
            text = _read_txt(path)
        elif ext == ".pdf":
            text = _read_pdf(path)
        elif ext in (".docx", ".doc"):
            text = _read_docx(path)
        else:
            log.error(f"Qo'llab-quvvatlanmagan format: {ext}")
            return []
        return parse_text(text)
    except Exception as e:
        log.error(f"Parser xatosi: {e}")
        return []


def _read_txt(path: str) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return ""


def _read_pdf(path: str) -> str:
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            t = p.extract_text()
            if t:
                pages.append(t)
    return "\n".join(pages)


def _read_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def parse_text(text: str) -> List[Dict]:
    """Matndan savollar ro'yxatini ajratib olish"""
    text = text.replace("\r\n", "\n")
    blocks = re.split(r"\n(?=\d+[\.\)])", "\n" + text.strip())
    questions = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        q = _parse_block(block)
        if q:
            questions.append(q)
    return questions


def _parse_block(block: str) -> Dict | None:
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if not lines:
        return None

    # Savol matni (1. yoki 1) ni olib tashlaymiz)
    q_text = re.sub(r"^\d+[\.\)]\s*", "", lines[0]).strip()

    q = {
        "type":             "multiple_choice",
        "question":         q_text,
        "options":          [],
        "correct":          None,
        "explanation":      "Izoh kiritilmagan.",
        "points":           1,
        "accepted_answers": [],
    }

    # TYPE:, IZOH:, BALL: qatorlarini topamiz
    for line in lines:
        ul = line.upper()
        if ul.startswith("TYPE:"):
            q["type"] = line[5:].strip().lower()
        elif ul.startswith("IZOH:"):
            q["explanation"] = line[5:].strip()
        elif ul.startswith("BALL:"):
            try:
                q["points"] = int(re.findall(r"\d+", line)[0])
            except Exception:
                pass

    t = q["type"]

    # ── 1. BIR JAVOBLI ────────────────────────────────────
    if t == "multiple_choice":
        for line in lines[1:]:
            if line.upper().startswith(("TYPE:", "IZOH:", "BALL:")):
                continue
            clean = line.replace("*", "").replace("=", "").strip()
            if not re.match(r"^[A-Za-z][\.\)]", clean):
                continue
            is_c = ("===") in line or "*" in line or "[TO'G'RI]" in line.upper()
            opt  = re.sub(r"\[TO'G'RI\]", "", line, flags=re.IGNORECASE)
            opt  = opt.replace("*", "").replace("=", "").strip()
            q["options"].append(opt)
            if is_c and not q["correct"]:
                q["correct"] = opt
        # Agar belgilash unutilgan bo'lsa — birinchi variant to'g'ri deb olinadi
        if q["options"] and not q["correct"]:
            q["correct"] = q["options"][0]

    # ── 2. KO'P JAVOBLI ───────────────────────────────────
    elif t == "multi_select":
        q["correct"] = []
        for line in lines[1:]:
            if line.upper().startswith(("TYPE:", "IZOH:", "BALL:")):
                continue
            clean = line.replace("*", "").replace("=", "").strip()
            if not re.match(r"^[A-Za-z][\.\)]", clean):
                continue
            is_c = "===" in line or "*" in line or "[TO'G'RI]" in line.upper()
            opt  = re.sub(r"\[TO'G'RI\]", "", line, flags=re.IGNORECASE)
            opt  = opt.replace("*", "").replace("=", "").strip()
            q["options"].append(opt)
            if is_c:
                q["correct"].append(opt)
        if q["options"] and not q["correct"]:
            q["correct"].append(q["options"][0])

    # ── 3. HA / YO'Q ──────────────────────────────────────
    elif t == "true_false":
        q["options"] = ["✅ Ha", "❌ Yo'q"]
        for line in lines[1:]:
            if line.upper().startswith("JAVOB:"):
                ans = line[6:].strip().lower()
                q["correct"] = "✅ Ha" if ans in ("ha", "true", "yes") else "❌ Yo'q"

    # ── 4. YOZMA JAVOB ────────────────────────────────────
    elif t in ("text_input", "fill_blank"):
        for line in lines[1:]:
            ul = line.upper()
            if ul.startswith("JAVOB:"):
                q["correct"] = line[6:].strip()
            elif ul.startswith("QABUL_QILINADIGAN:"):
                q["accepted_answers"] = [x.strip().lower() for x in line[18:].split(",")]

    # ── 5. MOSLASHTIRISH ──────────────────────────────────
    elif t == "matching":
        q["correct"] = {}
        for line in lines[1:]:
            if line.upper().startswith("CHAP:"):
                parts = line[5:].split("|")
                if len(parts) == 2:
                    q["correct"][parts[0].strip()] = parts[1].strip()

    # ── 6. TARTIBLASH ─────────────────────────────────────
    elif t == "ordering":
        q["correct"] = []
        for line in lines[1:]:
            if re.match(r"^\d+[\.\)]", line) and not line.upper().startswith("TYPE:"):
                q["correct"].append(line.strip())

    if q["correct"] or t in ("text_input", "fill_blank"):
        return q
    return None
