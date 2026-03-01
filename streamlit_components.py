"""
🌐 STREAMLIT HTML KOMPONENTLARI
static/ papkasidagi HTML fayllarni Streamlit da ko'rsatish
Streamlit Cloud da HTTPS orqali ishlaydi
"""
import json
import pathlib
import streamlit.components.v1 as components
import streamlit as st
from firebase.db import get_test, get_user_results, get_result_by_id

STATIC_DIR = pathlib.Path(__file__).parent / "static"


def _read_html(filename: str) -> str:
    """Static papkasidan HTML faylni o'qish"""
    path = STATIC_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"<p>❌ Fayl topilmadi: {filename}</p>"


def quiz_modal(test_id: str, height: int = 700) -> dict | None:
    """
    Test yechish modal oynasi
    test_id → Firebase dan test yuklab, HTML ga yuboradi
    Qaytaradi: {'type':'quiz_result', ...} yoki None
    """
    test = get_test(test_id)
    if not test:
        st.error(f"❌ Test topilmadi: {test_id}")
        return None

    html = _read_html("quiz_modal.html")

    # Test ma'lumotlarini HTML ga inject qilish
    test_json = json.dumps(test, ensure_ascii=False, default=str)
    inject_script = f"""
<script>
window.addEventListener('load', function() {{
  setTimeout(function() {{
    window.initTest({test_json});
  }}, 100);
}});
</script>
"""
    # </body> oldiga inject
    html = html.replace("</body>", inject_script + "</body>")

    result = components.html(html, height=height, scrolling=False)
    return result


def history_modal(user_id: int, limit: int = 100, height: int = 600) -> None:
    """
    Natijalar tarixi modal oynasi
    user_id → Firebase dan natijalar yuklab, HTML ga yuboradi
    """
    results = get_user_results(user_id, limit=limit)

    # Natijalarni serializatsiya
    results_json = json.dumps(results, ensure_ascii=False, default=str)

    html = _read_html("history_modal.html")
    inject_script = f"""
<script>
window.addEventListener('load', function() {{
  setTimeout(function() {{
    initHistory({results_json});
  }}, 100);
}});
</script>
"""
    html = html.replace("</body>", inject_script + "</body>")
    components.html(html, height=height, scrolling=False)


def create_test_modal(test_id: str = None, height: int = 800) -> dict | None:
    """
    Test yaratish / tahrirlash modal oynasi
    test_id berilsa — tahrirlash rejimi
    """
    html = _read_html("create_modal.html")

    if test_id:
        test = get_test(test_id)
        if test:
            test_json = json.dumps(test, ensure_ascii=False, default=str)
            inject_script = f"""
<script>
window.addEventListener('load', function() {{
  setTimeout(function() {{
    if (typeof loadEditData === 'function') loadEditData({test_json});
  }}, 150);
}});
</script>
"""
            html = html.replace("</body>", inject_script + "</body>")

    result = components.html(html, height=height, scrolling=True)
    return result
