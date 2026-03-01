"""
🌐 TELEGRAM WEBAPP SAHIFASI — Streamlit
Uch rejim URL parameter bilan boshqariladi:

  ?mode=test&test_id=ABC&user_id=123    → Test yechish
  ?mode=review&result_id=xxx&user_id=123 → Batafsil tahlil
  ?mode=history&user_id=123             → Natijalar tarixi
"""
import streamlit as st


def render_webapp():
    """Asosiy kirish nuqtasi — URL params bo'yicha yo'naltiradi."""
    params = st.query_params
    mode   = params.get("mode", "")
    uid_s  = params.get("user_id", "0")

    try:
        user_id = int(uid_s)
    except ValueError:
        user_id = 0

    # CSS
    st.markdown("""
    <style>
      #MainMenu, footer, header {visibility: hidden;}
      .block-container { padding: 1rem !important; }
      .webapp-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px; padding: 20px; color: white;
        margin-bottom: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
      }
      .q-card {
        background: white; border-radius: 12px; padding: 16px;
        margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
      }
      .correct-ans  { background: #d4edda; border-left-color: #28a745 !important; }
      .wrong-ans    { background: #f8d7da; border-left-color: #dc3545 !important; }
      .result-badge-pass { background:#28a745; color:white; padding:6px 14px;
                           border-radius:20px; font-weight:bold; }
      .result-badge-fail { background:#dc3545; color:white; padding:6px 14px;
                           border-radius:20px; font-weight:bold; }
      .stat-box { text-align:center; padding:12px; border-radius:10px;
                  background:#f8f9fa; margin:4px; }
      .stat-num  { font-size:2em; font-weight:bold; color:#667eea; }
    </style>
    """, unsafe_allow_html=True)

    if mode == "test":
        _render_test(user_id)
    elif mode == "review":
        _render_review(user_id)
    elif mode == "history":
        _render_history(user_id)
    else:
        st.title("🎓 Quiz Bot WebApp")
        st.info("Bu sahifa Telegram orqali ochilishi kerak.")


# ═══════════════════════════════════════════════════════════
# 1. TEST YECHISH
# ═══════════════════════════════════════════════════════════

def _render_test(user_id: int):
    params  = st.query_params
    test_id = params.get("test_id", "")

    if not test_id:
        st.error("❌ test_id parametri yo'q.")
        return

    # Session state init
    if "wa_test_id" not in st.session_state or st.session_state.wa_test_id != test_id:
        st.session_state.wa_test_id    = test_id
        st.session_state.wa_answers    = {}
        st.session_state.wa_current    = 0
        st.session_state.wa_submitted  = False
        st.session_state.wa_result     = None
        st.session_state.wa_start_time = __import__("time").time()

    # Test ma'lumotlarini olish
    if "wa_test_data" not in st.session_state or st.session_state.wa_test_id != test_id:
        try:
            from firebase.db import get_test
            test = get_test(test_id)
        except Exception as e:
            st.error(f"❌ Test yuklanmadi: {e}")
            return
        if not test:
            st.error("❌ Test topilmadi.")
            return
        st.session_state.wa_test_data = test

    test = st.session_state.wa_test_data
    qs   = test.get("questions", [])

    if not qs:
        st.error("❌ Bu testda savollar yo'q.")
        return

    if st.session_state.wa_submitted and st.session_state.wa_result:
        _show_test_result(test, st.session_state.wa_result, user_id)
        return

    # Header
    idx      = st.session_state.wa_current
    progress = (idx) / len(qs)
    st.markdown(f"""
    <div class="webapp-card">
      <h3>📝 {test.get('title', 'Test')}</h3>
      <p>📁 {test.get('category', '')} &nbsp;|&nbsp;
         📋 {len(qs)} savol &nbsp;|&nbsp;
         🎯 O'tish: {test.get('passing_score', 60)}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.progress(progress, text=f"Savol {idx+1}/{len(qs)}")

    if idx < len(qs):
        q = qs[idx]
        _render_question(q, idx, len(qs))

        col1, col2 = st.columns([1, 1])
        if idx > 0:
            with col1:
                if st.button("⬅️ Oldingi", use_container_width=True):
                    st.session_state.wa_current -= 1
                    st.rerun()

        can_next = str(idx) in st.session_state.wa_answers
        with col2:
            if idx < len(qs) - 1:
                if st.button("Keyingi ➡️", disabled=not can_next, use_container_width=True):
                    st.session_state.wa_current += 1
                    st.rerun()
            else:
                answered = len(st.session_state.wa_answers)
                if st.button(
                    f"✅ Yakunlash ({answered}/{len(qs)})",
                    disabled=(answered == 0),
                    use_container_width=True,
                    type="primary"
                ):
                    _submit_test(test, user_id)
                    st.rerun()

    # Mini progress map
    st.markdown("**Savollar holati:**")
    cols = st.columns(min(len(qs), 10))
    for i in range(len(qs)):
        c   = cols[i % len(cols)]
        ans = st.session_state.wa_answers.get(str(i))
        ico = "✅" if ans else ("📍" if i == idx else "⬜")
        if c.button(ico, key=f"nav_{i}", use_container_width=True):
            st.session_state.wa_current = i
            st.rerun()


def _render_question(q: dict, idx: int, total: int):
    q_type = q.get("type", "multiple_choice")
    q_text = q.get("question", q.get("text", ""))

    st.markdown(f"""
    <div class="q-card">
      <b>Savol {idx+1}.</b> {q_text}
    </div>
    """, unsafe_allow_html=True)

    key = f"ans_{idx}"

    if q_type in ("multiple_choice", "true_false"):
        opts = q.get("options", ["✅ Ha", "❌ Yo'q"])
        labels = []
        for opt in opts:
            lbl = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
            labels.append(lbl)
        cur = st.session_state.wa_answers.get(str(idx))
        cur_idx = None
        if cur:
            import re as _re
            m = _re.match(r"^([A-Za-z])", str(cur))
            if m:
                li = ord(m.group(1).upper()) - ord("A")
                if 0 <= li < len(labels):
                    cur_idx = li
        sel = st.radio("Javobni tanlang:", labels, index=cur_idx,
                       key=key, horizontal=False)
        if sel:
            LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
            chosen_idx = labels.index(sel)
            st.session_state.wa_answers[str(idx)] = LETTERS[chosen_idx]

    elif q_type == "multi_select":
        opts = q.get("options", [])
        labels = [str(o).split(")", 1)[-1].strip() if ")" in str(o) else str(o) for o in opts]
        cur = st.session_state.wa_answers.get(str(idx), [])
        cur_idxs = []
        if isinstance(cur, list):
            LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
            import re as _re
            for c in cur:
                m = _re.match(r"^([A-Za-z])", str(c))
                if m:
                    li = ord(m.group(1).upper()) - ord("A")
                    if 0 <= li < len(labels):
                        cur_idxs.append(li)
        selected = []
        for i, lbl in enumerate(labels):
            checked = st.checkbox(lbl, value=(i in cur_idxs), key=f"{key}_{i}")
            if checked:
                LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
                selected.append(LETTERS[i])
        if selected:
            st.session_state.wa_answers[str(idx)] = selected

    elif q_type in ("text_input", "fill_blank"):
        cur = st.session_state.wa_answers.get(str(idx), "")
        val = st.text_input("Javobingizni yozing:", value=cur, key=key)
        if val.strip():
            st.session_state.wa_answers[str(idx)] = val.strip()


def _submit_test(test: dict, user_id: int):
    """Testni yakunlash, natijani saqlash."""
    import time as _t
    from utils.scoring import calculate_score
    from firebase.db import save_result

    qs      = test.get("questions", [])
    answers = st.session_state.wa_answers
    elapsed = int(_t.time() - st.session_state.get("wa_start_time", _t.time()))

    scored = calculate_score(qs, answers)
    scored["time_spent"]    = elapsed
    scored["passing_score"] = test.get("passing_score", 60)
    scored["mode"]          = "webapp"

    try:
        rid = save_result(user_id, test.get("test_id"), scored)
        scored["result_id"] = rid
    except Exception as e:
        st.warning(f"Natija saqlanmadi: {e}")
        scored["result_id"] = "local"

    st.session_state.wa_result    = scored
    st.session_state.wa_submitted = True


def _show_test_result(test: dict, res: dict, user_id: int):
    pct    = res.get("percentage", 0)
    passed = pct >= test.get("passing_score", 60)
    m, s   = divmod(res.get("time_spent", 0), 60)

    badge = "result-badge-pass" if passed else "result-badge-fail"
    text  = "🎉 MUVAFFAQIYATLI!" if passed else "❌ YIQILDINGIZ"

    st.markdown(f"""
    <div class="webapp-card" style="text-align:center">
      <h2>{res.get('emoji','📊')} TEST YAKUNLANDI</h2>
      <h1 style="font-size:3em">{pct}%</h1>
      <span class="{badge}">{text}</span>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="stat-box"><div class="stat-num">{res.get("correct_count",0)}</div>✅ To\'g\'ri</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-box"><div class="stat-num">{res.get("wrong_count",0)}</div>❌ Xato</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-box"><div class="stat-num">{res.get("skipped_count",0)}</div>⏭ O\'tkazilgan</div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-box"><div class="stat-num">{m}:{s:02d}</div>⏱ Vaqt</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Qaytadan ishlash", use_container_width=True):
        for k in ["wa_answers","wa_current","wa_submitted","wa_result","wa_test_data","wa_test_id","wa_start_time"]:
            st.session_state.pop(k, None)
        st.rerun()

    # Batafsil tahlil
    rid = res.get("result_id", "")
    if rid and rid != "local":
        with st.expander("🔍 Batafsil tahlil ko'rish"):
            _render_detailed_results(
                test.get("questions", []),
                res.get("detailed_results", [])
            )


# ═══════════════════════════════════════════════════════════
# 2. BATAFSIL TAHLIL (review)
# ═══════════════════════════════════════════════════════════

def _render_review(user_id: int):
    params    = st.query_params
    result_id = params.get("result_id", "")

    if not result_id:
        st.error("❌ result_id parametri yo'q.")
        return

    try:
        from firebase.db import get_result_by_id, get_test
        res  = get_result_by_id(result_id)
    except Exception as e:
        st.error(f"❌ Natija yuklanmadi: {e}")
        return

    if not res:
        st.error("❌ Natija topilmadi.")
        return

    test     = get_test(res.get("test_id", ""))
    pct      = res.get("percentage", 0)
    passed   = res.get("passed", False)
    badge    = "result-badge-pass" if passed else "result-badge-fail"
    badge_t  = "✅ MUVAFFAQIYATLI" if passed else "❌ YIQILDI"
    m, s     = divmod(res.get("time_spent", 0), 60)

    title    = test.get("title", "Test") if test else "Test"

    st.markdown(f"""
    <div class="webapp-card">
      <h3>🔍 BATAFSIL TAHLIL</h3>
      <h4>📝 {title}</h4>
      <p>📅 Natija ID: {result_id[:8]}...</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Natija",   f"{pct}%")
    c2.metric("✅ To'g'ri",  res.get("correct_count", 0))
    c3.metric("❌ Xato",     res.get("wrong_count", 0))
    c4.metric("⏱ Vaqt",     f"{m}:{s:02d}")

    st.markdown(f'<span class="{badge}">{badge_t}</span><br><br>', unsafe_allow_html=True)
    st.markdown("---")

    questions = test.get("questions", []) if test else []
    detailed  = res.get("detailed_results", [])

    if not detailed:
        st.info("Bu test uchun batafsil tahlil mavjud emas.")
        return

    st.subheader("📋 Har bir savol tahlili")
    _render_detailed_results(questions, detailed)


def _render_detailed_results(questions: list, detailed: list):
    """Savollar tahlilini ko'rsatish."""
    for d in detailed:
        idx   = d.get("question_index", 0)
        is_c  = d.get("is_correct", False)
        u_ans = d.get("user_answer") or "Belgilanmagan"
        c_ans = d.get("correct_answer", "?")
        expl  = d.get("explanation", "")

        q_obj  = questions[idx] if idx < len(questions) else {}
        q_text = (d.get("question_text")
                  or q_obj.get("question", q_obj.get("text", f"{idx+1}-savol")))

        pts   = d.get("earned_points", 0)
        maxp  = d.get("max_points", 1)
        cls   = "correct-ans" if is_c else "wrong-ans"
        icon  = "✅" if is_c else "❌"

        st.markdown(f"""
        <div class="q-card {cls}">
          <b>{icon} Savol {idx+1}</b> [{pts}/{maxp} ball]<br>
          <i>{q_text}</i>
        </div>
        """, unsafe_allow_html=True)

        if not is_c:
            col1, col2 = st.columns(2)
            col1.error(f"👤 Siz: **{str(u_ans)[:60]}**")
            col2.success(f"🎯 To'g'ri: **{str(c_ans)[:60]}**")
        else:
            st.success(f"✔️ Javob: **{str(c_ans)[:60]}**")

        if expl and expl not in ("Izoh kiritilmagan.", "Izoh yo'q", "Izoh kiritilmagan", ""):
            st.info(f"💡 {expl}")


# ═══════════════════════════════════════════════════════════
# 3. NATIJALAR TARIXI (history)
# ═══════════════════════════════════════════════════════════

def _render_history(user_id: int):
    if not user_id:
        st.error("❌ user_id parametri yo'q.")
        return

    st.markdown("""
    <div class="webapp-card">
      <h3>📜 NATIJALAR TARIXI</h3>
    </div>
    """, unsafe_allow_html=True)

    # Natijalarni yuklab olish
    try:
        from firebase.db import get_user_results
        results = get_user_results(user_id, limit=100)
    except Exception as e:
        st.error(f"❌ Natijalar yuklanmadi: {e}")
        return

    if not results:
        st.info("📭 Siz hali hech qanday test ishlamagansiz.")
        return

    # Umumiy statistika
    total   = len(results)
    avg_pct = round(sum(r.get("percentage", 0) for r in results) / total, 1) if total else 0
    best    = max((r.get("percentage", 0) for r in results), default=0)
    passed  = sum(1 for r in results if r.get("passed"))

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="stat-box"><div class="stat-num">{total}</div>📋 Jami</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-box"><div class="stat-num">{avg_pct}%</div>📊 O\'rtacha</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-box"><div class="stat-num">{best}%</div>🏆 Eng yaxshi</div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-box"><div class="stat-num">{passed}</div>✅ O\'tilgan</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Fan filtri
    cats = sorted(set(r.get("test_title", "")[:15] for r in results if r.get("test_title")))
    sel  = st.selectbox("📁 Fan bo'yicha filtr:", ["Hammasi"] + cats)

    filtered = results if sel == "Hammasi" else [
        r for r in results if r.get("test_title", "").startswith(sel)
    ]

    st.markdown(f"**{len(filtered)} ta natija ko'rsatilmoqda:**")

    for r in filtered:
        pct    = r.get("percentage", 0)
        passed = r.get("passed", False)
        title  = r.get("test_title", "Noma'lum test")[:30]
        mode   = "📊 Poll" if r.get("mode") == "poll" else "▶️ Inline" if r.get("mode") == "inline" else "🌐 Web"
        icon   = "✅" if passed else "❌"
        rid    = r.get("result_id", "")

        # Sana
        dt_str = "--"
        try:
            dt = r.get("completed_at")
            if dt and hasattr(dt, "timestamp"):
                from datetime import datetime, timezone
                dt_str = datetime.fromtimestamp(float(dt.timestamp()), tz=timezone.utc).strftime("%d.%m.%Y %H:%M")
            elif dt and hasattr(dt, "strftime"):
                dt_str = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass

        with st.expander(f"{icon} {title} — {pct}% | {dt_str}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Natija", f"{pct}%")
            c2.metric("Rejim", mode)
            c3.metric("Holat", "✅ O'tdi" if passed else "❌ Yiqildi")
            st.caption(f"ID: {rid[:12]}...")

            detailed = r.get("detailed_results", [])
            if detailed and st.button("🔍 Ko'rish", key=f"det_{rid[:8]}"):
                _render_detailed_results([], detailed)
