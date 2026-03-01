"""
📄 FAYL PARSER — TXT / PDF / DOCX
Universal format: bot ham, HTML ham tushunadi
Savollar Firestore ga saqlanadi:
  text/question : savol matni
  options       : ["Toshkent", "Moskva", ...]  — toza, harfsiz
  correct       : 0  (index, HTML uchun)
  correct_letter: "A"  (harf, bot uchun)
  type          : "multiple_choice" / "true_false" / "text_input" / ...
"""
import re
import logging
from pathlib import Path
from typing import List, Dict

log = logging.getLogger(__name__)
LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


def parse_file(path: str) -> List[Dict]:
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


def _clean_opt(line: str) -> str:
    """'A) Toshkent' → 'Toshkent' — harfni olib tashlaydi"""
    s = re.sub(r"\[TO'G'RI\]", "", line, flags=re.IGNORECASE)
    s = s.replace("*", "").replace("=", "").strip()
    s = re.sub(r"^[A-Za-z][\.\)]\s*", "", s).strip()
    return s


def _parse_block(block: str) -> Dict | None:
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if not lines:
        return None

    # Savol matni — boshidagi raqamni olib tashlaymiz
    q_text = re.sub(r"^\d+[\.\)]\s*", "", lines[0]).strip()

    q = {
        # Ikkala format uchun
        "question":         q_text,   # bot ishlatadi
        "text":             q_text,   # HTML ishlatadi
        "type":             "multiple_choice",
        "options":          [],       # toza matn (harfsiz)
        "correct":          None,     # HTML: index (0, 1, 2...)
        "correct_letter":   None,     # Bot: "A", "B", "C"
        "explanation":      "",
        "points":           1,
        "accepted_answers": [],
    }

    # META qatorlar
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
            raw = line.replace("*", "").replace("=", "").strip()
            if not re.match(r"^[A-Za-z][\.\)]", raw):
                continue
            is_c = "===" in line or "*" in line or "[TO'G'RI]" in line.upper()
            opt_clean = _clean_opt(line)
            q["options"].append(opt_clean)
            if is_c and q["correct"] is None:
                idx = len(q["options"]) - 1
                q["correct"]        = idx
                q["correct_letter"] = LETTERS[idx] if idx < len(LETTERS) else "A"

        if q["options"] and q["correct"] is None:
            q["correct"]        = 0
            q["correct_letter"] = "A"

    # ── 2. KO'P JAVOBLI ───────────────────────────────────
    elif t == "multi_select":
        q["correct"] = []
        q["correct_letter"] = []
        for line in lines[1:]:
            if line.upper().startswith(("TYPE:", "IZOH:", "BALL:")):
                continue
            raw = line.replace("*", "").replace("=", "").strip()
            if not re.match(r"^[A-Za-z][\.\)]", raw):
                continue
            is_c = "===" in line or "*" in line or "[TO'G'RI]" in line.upper()
            opt_clean = _clean_opt(line)
            q["options"].append(opt_clean)
            if is_c:
                idx = len(q["options"]) - 1
                q["correct"].append(idx)
                q["correct_letter"].append(LETTERS[idx] if idx < len(LETTERS) else "A")

        if q["options"] and not q["correct"]:
            q["correct"]        = [0]
            q["correct_letter"] = ["A"]

    # ── 3. HA / YO'Q ──────────────────────────────────────
    elif t == "true_false":
        q["options"] = ["Ha", "Yo'q"]
        q["correct"] = 0
        q["correct_letter"] = "A"
        for line in lines[1:]:
            if line.upper().startswith("JAVOB:"):
                ans = line[6:].strip().lower()
                if ans in ("ha", "true", "yes", "1"):
                    q["correct"]        = 0
                    q["correct_letter"] = "A"
                else:
                    q["correct"]        = 1
                    q["correct_letter"] = "B"

    # ── 4. YOZMA JAVOB ────────────────────────────────────
    elif t in ("text_input", "fill_blank"):
        for line in lines[1:]:
            ul = line.upper()
            if ul.startswith("JAVOB:"):
                q["correct"]       = line[6:].strip()
                q["correct_letter"] = line[6:].strip()
            elif ul.startswith("QABUL_QILINADIGAN:"):
                q["accepted_answers"] = [x.strip().lower() for x in line[18:].split(",")]

    # ── 5. MOSLASHTIRISH ──────────────────────────────────
    elif t == "matching":
        q["correct"] = {}
        q["pairs"]   = []
        for line in lines[1:]:
            if line.upper().startswith("CHAP:"):
                parts = line[5:].split("|")
                if len(parts) == 2:
                    left  = parts[0].strip()
                    right = parts[1].strip()
                    q["pairs"].append({"left": left, "right": right})
                    q["correct"][left] = right

    # ── 6. TARTIBLASH ─────────────────────────────────────
    elif t == "ordering":
        q["correct"] = []
        q["words"]   = []
        for line in lines[1:]:
            if re.match(r"^\d+[\.\)]", line) and not line.upper().startswith("TYPE:"):
                word = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
                q["correct"].append(word)
                q["words"].append(word)

    if q["correct"] is not None or t in ("text_input", "fill_blank"):
        return q
    return None
