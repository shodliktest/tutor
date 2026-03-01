"""
👤 PROFIL, NATIJALAR (8 tadan + sahifalash) va MENING TESTLARIM (5 tadan + sahifalash)
Tahlil — modal alert oyna orqali chiroyli ko'rsatish
Test kartochkasi — chapga/o'ngga knopkalar
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from firebase.db import get_user, get_user_results, get_test, get_my_tests
from keyboards.keyboards import main_reply_keyboard

log = logging.getLogger(__name__)
router = Router()

PAGE_SIZE_RESULTS = 8   # Natijalar sahifasida nechta
PAGE_SIZE_TESTS   = 5   # Mening testlarim sahifasida nechta


# ═══════════════════════════════════════════════════════════
# 1. PROFIL
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "👤 Profil")
async def profile_msg(message: Message):
    await _show_profile(message, message.from_user.id)


@router.callback_query(F.data == "profile_view")
async def profile_cb(callback: CallbackQuery):
    await callback.answer()
    await _show_profile(callback.message, callback.from_user.id, edit=True)


async def _show_profile(msg, uid: int, edit: bool = False):
    user = get_user(uid)
    if not user:
        text = "❌ Profil topilmadi. /start ni bosing."
        await (msg.edit_text(text) if edit else msg.answer(text))
        return

    role_map = {"admin": "👑 Admin", "teacher": "👨‍🏫 O'qituvchi", "user": "🎓 O'quvchi"}
    role = role_map.get(user.get("role", "user"), "🎓 O'quvchi")
    avg  = round(user.get("avg_score", 0), 1)
    total = user.get("total_tests", 0)

    # Badge hisoblash
    badges = []
    if total >= 1:   badges.append("🥉 Boshliqchi")
    if total >= 10:  badges.append("🥈 Tajribali")
    if total >= 50:  badges.append("🥇 Ustoz")
    if avg >= 90:    badges.append("🌟 Mukammal")
    if avg >= 80:    badges.append("🔥 A'lochi")
    badge_str = "  ".join(badges) if badges else "Hali yo'q"

    text = (
        f"👤 <b>SHAXSIY PROFIL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"👤 Ism: <b>{user.get('name', 'Noma\'lum')}</b>\n"
        f"🎭 Rol: <b>{role}</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Yechilgan testlar: <b>{total} ta</b>\n"
        f"📊 O'rtacha natija: <b>{avg}%</b>\n"
        f"🏅 Yutuqlar: {badge_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Natijalarim tarixi", callback_data="results_p0"))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    kb = builder.as_markup()

    try:
        if edit:
            await msg.edit_text(text, reply_markup=kb)
        else:
            await msg.answer(text, reply_markup=kb)
    except TelegramBadRequest:
        await msg.answer(text, reply_markup=kb)


# ═══════════════════════════════════════════════════════════
# 2. NATIJALAR TARIXI — 8 tadan, sahifalash
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "📊 Natijalarim")
async def results_msg(message: Message):
    await _show_results(message, message.from_user.id, page=0)


@router.callback_query(F.data.startswith("results_p"))
async def results_page_cb(callback: CallbackQuery):
    await callback.answer()
    page = int(callback.data[9:])
    await _show_results(callback.message, callback.from_user.id, page=page, edit=True)


async def _show_results(msg, uid: int, page: int = 0, edit: bool = False):
    all_results = get_user_results(uid, limit=200)

    if not all_results:
        text = (
            "📭 <b>NATIJALAR TARIXI</b>\n\n"
            "Siz hali hech qanday test ishlamagansiz.\n"
            "Testlar bo'limidan boshlang! 🚀"
        )
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📚 Testlarga o'tish", callback_data="go_tests"))
        try:
            if edit: await msg.edit_text(text, reply_markup=builder.as_markup())
            else:    await msg.answer(text, reply_markup=builder.as_markup())
        except TelegramBadRequest:
            await msg.answer(text, reply_markup=builder.as_markup())
        return

    total_pages = (len(all_results) + PAGE_SIZE_RESULTS - 1) // PAGE_SIZE_RESULTS
    page = max(0, min(page, total_pages - 1))
    chunk = all_results[page * PAGE_SIZE_RESULTS:(page + 1) * PAGE_SIZE_RESULTS]

    text = (
        f"📋 <b>NATIJALAR TARIXI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Sahifa {page+1}/{total_pages} | Jami: {len(all_results)} ta</i>\n\n"
    )

    builder = InlineKeyboardBuilder()
    for res in chunk:
        test  = get_test(res.get("test_id", ""))
        title = (test.get("title", "O'chirilgan")[:22] if test else "Noma'lum test")
        icon  = "✅" if res.get("passed") else "❌"
        pct   = res.get("percentage", 0)
        mode  = "📊" if res.get("mode") == "poll" else "▶️"
        dt    = res.get("completed_at")
        date  = ""
        try:
            if dt and hasattr(dt, "strftime"):
                date = dt.strftime("%d.%m")
            elif dt and hasattr(dt, "timestamp"):
                from datetime import datetime, timezone
                date = datetime.fromtimestamp(float(dt.timestamp()), tz=timezone.utc).strftime("%d.%m")
        except Exception:
            date = "--"

        rid = res.get("result_id", "")
        text += f"{icon} {mode} <b>{title}</b>\n   📊 {pct}% | 📅 {date}\n\n"
        builder.row(InlineKeyboardButton(
            text=f"{icon} {title[:18]} — {pct}%",
            callback_data=f"res_detail_{rid}"
        ))

    # Sahifa navigatsiyasi
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"results_p{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"results_p{page+1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))

    try:
        if edit: await msg.edit_text(text, reply_markup=builder.as_markup())
        else:    await msg.answer(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        await msg.answer(text, reply_markup=builder.as_markup())


# ═══════════════════════════════════════════════════════════
# 3. TEST NATIJASI KARTOCHKASI — chapga/o'ngga navigatsiya
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("res_detail_"))
async def result_detail(callback: CallbackQuery):
    await callback.answer()
    rid = callback.data[11:]
    await _show_result_card(callback, rid)


async def _show_result_card(callback: CallbackQuery, rid: str):
    from firebase.db import get_result_by_id
    res  = get_result_by_id(rid)
    if not res:
        return await callback.message.answer("❌ Natija topilmadi.")

    test  = get_test(res.get("test_id", ""))
    title = test.get("title", "Noma'lum") if test else "O'chirilgan test"
    cat   = test.get("category", "") if test else ""

    pct    = res.get("percentage", 0)
    passed = res.get("passed", False)
    mode   = "📊 Poll" if res.get("mode") == "poll" else "▶️ Inline"
    m, s   = divmod(res.get("time_spent", 0), 60)

    dt_str = "--"
    try:
        dt = res.get("completed_at")
        if dt and hasattr(dt, "timestamp"):
            from datetime import datetime, timezone
            dt_str = datetime.fromtimestamp(float(dt.timestamp()), tz=timezone.utc).strftime("%d.%m.%Y %H:%M")
        elif dt and hasattr(dt, "strftime"):
            dt_str = dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        pass

    text = (
        f"{'✅' if passed else '❌'} <b>TEST NATIJASI KARTOCHKASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{title}</b>\n"
        f"📁 Fan: {cat}\n"
        f"🎮 Rejim: {mode}\n"
        f"📅 Sana: {dt_str}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 O'zlashtirish: <b>{pct}%</b>\n"
        f"✅ To'g'ri: <b>{res.get('correct_count', 0)}</b>   "
        f"❌ Xato: <b>{res.get('wrong_count', 0)}</b>   "
        f"⏭ O'tkazilgan: <b>{res.get('skipped_count', 0)}</b>\n"
        f"⏱ Vaqt: <b>{m}:{s:02d}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{'🎉 MUVAFFAQIYATLI!' if passed else '❌ YIQILDINGIZ'}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔍 Batafsil tahlil (modal)",
        callback_data=f"analysis_{rid}"
    ))
    if test:
        builder.row(
            InlineKeyboardButton(text="🔄 Qaytadan",  callback_data=f"start_test_{res.get('test_id')}"),
            InlineKeyboardButton(text="📤 Ulashish",  callback_data=f"share_test_{res.get('test_id')}"),
        )
    builder.row(InlineKeyboardButton(text="⬅️ Natijalar", callback_data="results_p0"))

    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=builder.as_markup())


# ═══════════════════════════════════════════════════════════
# 4. BATAFSIL TAHLIL — Modal alert oyna orqali (show_alert=True)
# ═══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("analysis_"))
async def analysis_modal(callback: CallbackQuery):
    """Tahlilni modal-uslub oynada ko'rsatish — bitta chiroyli xabar"""
    rid = callback.data[9:]
    from firebase.db import get_result_by_id
    res = get_result_by_id(rid)

    if not res:
        return await callback.answer("❌ Natija topilmadi.", show_alert=True)

    test      = get_test(res.get("test_id", ""))
    detailed  = res.get("detailed_results", [])
    questions = test.get("questions", []) if test else []

    if not detailed:
        return await callback.answer(
            "⚠️ Bu test uchun batafsil tahlil mavjud emas.\n"
            "(Eski versiyada ishlangan testlar uchun saqlanmagan)",
            show_alert=True
        )

    total   = len(detailed)
    correct = sum(1 for d in detailed if d.get("is_correct"))
    wrong   = total - correct
    title   = test.get("title", "Test").upper() if test else "TEST"
    pct     = res.get("percentage", 0)
    passed  = res.get("passed", False)

    # ── 1. MODAL POPUP (show_alert) — qisqa xulosa ──────────
    alert_text = (
        f"{'🏆' if passed else '❌'} {title}\n"
        f"{'━'*20}\n"
        f"📊 Natija: {pct}%\n"
        f"✅ To'g'ri: {correct}/{total}\n"
        f"❌ Xato:   {wrong}/{total}\n"
        f"{'━'*20}\n"
        f"{'🎉 MUVAFFAQIYATLI!' if passed else '😔 YIQILDINGIZ'}\n"
        f"↓ Batafsil tahlil quyida"
    )
    await callback.answer(alert_text, show_alert=True)
    STATUS    = "🏆 MUVAFFAQIYATLI" if passed else "❌ YIQILDI"
    bar_full  = "🟩"
    bar_empty = "🟥"
    bar_len   = 10
    filled    = round(pct / 100 * bar_len)
    bar       = bar_full * filled + bar_empty * (bar_len - filled)

    # ── HEADER (modal uslubi) ──────────────────────
    header = (
        f"╔══════════════════════╗\n"
        f"║  📊 BATAFSIL TAHLIL  ║\n"
        f"╚══════════════════════╝\n\n"
        f"📝 <b>{title}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{bar}  <b>{pct}%</b>\n"
        f"✅ To'g'ri: <b>{correct}</b>   ❌ Xato: <b>{wrong}</b>   📋 Jami: <b>{total}</b>\n"
        f"<b>{STATUS}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # ── Savollar tahlili ──────────────────────────
    body = ""
    for d in detailed:
        i     = d.get("question_index", 0)
        is_c  = d.get("is_correct", False)
        u_ans = d.get("user_answer") or "—"
        c_ans = d.get("correct_answer", "?")
        q_obj = questions[i] if i < len(questions) else {}
        q_txt = q_obj.get("question", q_obj.get("text", f"{i+1}-savol"))
        expl  = q_obj.get("explanation", "")
        pts   = d.get("earned_points", 0)
        max_p = d.get("max_points", 1)

        icon  = "✅" if is_c else "❌"
        line  = f"{icon} <b>{i+1}.</b> <i>{q_txt[:90]}{'...' if len(q_txt)>90 else ''}</i>\n"

        if not is_c:
            line += (
                f"   👤 Siz: <code>{str(u_ans)[:45]}</code>\n"
                f"   🎯 To'g'ri: <code>{str(c_ans)[:45]}</code>\n"
            )
        else:
            line += f"   ✔️ <code>{str(c_ans)[:50]}</code>\n"

        clean_expl = (expl or "").strip()
        if clean_expl and clean_expl not in ("Izoh kiritilmagan.", "Izoh yo'q", "Izoh kiritilmagan"):
            line += f"   💡 <i>{clean_expl[:75]}{'...' if len(clean_expl)>75 else ''}</i>\n"

        line += f"   📌 Ball: {pts}/{max_p}\n\n"
        body += line

    close_builder = InlineKeyboardBuilder()
    close_builder.row(
        InlineKeyboardButton(text="🔄 Qaytadan ishlash", callback_data=f"start_test_{res.get('test_id')}"),
        InlineKeyboardButton(text="⬅️ Natijaga qaytish", callback_data=f"res_detail_{rid}"),
    )
    close_builder.row(
        InlineKeyboardButton(text="🚮 Tahlilni yopish", callback_data=f"close_analysis"),
    )

    # Agar juda uzun bo'lsa — bo'lib yuboramiz
    full = header + body
    max_chunk = 3800
    if len(full) <= max_chunk:
        await callback.message.answer(full, reply_markup=close_builder.as_markup())
    else:
        chunks = []
        current = header
        for line in body.split("\n\n"):
            block = line + "\n\n"
            if len(current) + len(block) > max_chunk:
                chunks.append(current)
                current = ""
            current += block
        if current.strip():
            chunks.append(current)

        for idx, chunk in enumerate(chunks):
            if idx == len(chunks) - 1:
                await callback.message.answer(chunk, reply_markup=close_builder.as_markup())
            else:
                await callback.message.answer(chunk)


@router.callback_query(F.data == "close_analysis")
async def close_analysis(callback: CallbackQuery):
    """Tahlil xabarini o'chirish"""
    await callback.answer("🚮 Tahlil yopildi")
    try:
        await callback.message.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("dl_result_"))
async def download_result_txt(callback: CallbackQuery):
    """Test natijasini TXT formatda yuklab olish — creator info + vaqt"""
    await callback.answer("⏳ TXT tayyorlanmoqda...")
    rid = callback.data[10:]
    from firebase.db import get_result_by_id
    import datetime as _dt
    res = get_result_by_id(rid)
    if not res:
        return await callback.answer("❌ Natija topilmadi.", show_alert=True)

    test      = get_test(res.get("test_id", ""))
    detailed  = res.get("detailed_results", [])
    questions = test.get("questions", []) if test else []
    user      = callback.from_user
    bot_info  = await callback.bot.me()

    now  = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    uname  = f"@{user.username}" if user.username else f"id:{user.id}"
    ufull  = user.full_name or user.first_name or ""
    bname  = bot_info.username if bot_info else "bot"

    title = test.get("title", "Test") if test else "Test"
    pct   = res.get("percentage", 0)
    passed = res.get("passed", False)
    correct = res.get("correct_count", 0)
    wrong   = res.get("wrong_count", 0)
    total   = len(detailed) or correct + wrong

    lines = [
        f"# ═══════════════════════════════════",
        f"# TEST NATIJASI",
        f"# ═══════════════════════════════════",
        f"# Foydalanuvchi: {ufull} {uname}",
        f"# Bot: @{bname}",
        f"# Yuklab olindi: {now}",
        f"# ─────────────────────────────────",
        f"# Test: {title}",
        f"# Natija: {pct}%  {'✓ MUVAFFAQIYATLI' if passed else '✗ YIQILDI'}",
        f"# To'g'ri: {correct}/{total}  |  Xato: {wrong}/{total}",
        f"# ═══════════════════════════════════",
        "",
    ]

    for d in detailed:
        i     = d.get("question_index", 0)
        is_c  = d.get("is_correct", False)
        u_ans = d.get("user_answer") or "—"
        c_ans = d.get("correct_answer", "?")
        q_obj = questions[i] if i < len(questions) else {}
        q_txt = q_obj.get("question", q_obj.get("text", f"{i+1}-savol"))
        expl  = q_obj.get("explanation", "")

        lines.append(f"{'✓' if is_c else '✗'} {i+1}. {q_txt}")
        if not is_c:
            lines.append(f"   Siz: {u_ans}")
            lines.append(f"   To'g'ri: {c_ans}")
        else:
            lines.append(f"   Javob: {c_ans}")
        clean_e = (expl or "").strip()
        if clean_e and clean_e not in ("Izoh kiritilmagan.", "Izoh yo'q", "Izoh kiritilmagan"):
            lines.append(f"   Izoh: {clean_e}")
        lines.append("")

    txt = "\n".join(lines)
    fname = f"Natija_{title[:20]}_{now[:10]}.txt"
    doc = BufferedInputFile(txt.encode("utf-8"), filename=fname)
    await callback.message.answer_document(
        doc,
        caption=(
            f"📄 <b>{title}</b> — natija\n"
            f"👤 {ufull} {uname}\n"
            f"📊 {pct}% | {'✅ O\'tdi' if passed else '❌ Yiqildi'}"
        )
    )


# ═══════════════════════════════════════════════════════════
# 5. MENING TESTLARIM — 5 tadan, sahifalash, ulashish, TXT
# ═══════════════════════════════════════════════════════════

@router.message(F.text == "🗂 Mening testlarim")
async def my_tests_handler(message: Message):
    await _show_my_tests(message, message.from_user.id, page=0)


@router.callback_query(F.data.startswith("mytests_p"))
async def my_tests_page(callback: CallbackQuery):
    await callback.answer()
    page = int(callback.data[9:])
    await _show_my_tests(callback.message, callback.from_user.id, page=page, edit=True)


async def _show_my_tests(msg, uid: int, page: int = 0, edit: bool = False):
    tests = get_my_tests(uid)

    if not tests:
        text = (
            "📭 <b>MENING TESTLARIM</b>\n\n"
            "Siz hali test yaratmagansiz.\n"
            "➕ Test Yaratish bo'limidan boshlang!"
        )
        try:
            if edit: await msg.edit_text(text)
            else:    await msg.answer(text)
        except TelegramBadRequest:
            await msg.answer(text)
        return

    total_pages = (len(tests) + PAGE_SIZE_TESTS - 1) // PAGE_SIZE_TESTS
    page = max(0, min(page, total_pages - 1))
    chunk = tests[page * PAGE_SIZE_TESTS:(page + 1) * PAGE_SIZE_TESTS]

    text = (
        f"🗂 <b>MENING TESTLARIM</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Sahifa {page+1}/{total_pages} | Jami: {len(tests)} ta</i>\n\n"
    )
    builder = InlineKeyboardBuilder()

    for t in chunk:
        tid   = t.get("test_id", "")
        title = t.get("title", "Nomsiz")
        cat   = t.get("category", "")
        vis   = {"public": "🌍", "link": "🔗", "private": "🔒"}.get(t.get("visibility"), "")
        sc    = t.get("solve_count", 0)
        avg   = round(t.get("avg_score", 0), 1)
        qc    = len(t.get("questions", []))

        text += (
            f"{vis} <b>{title}</b> <code>[{tid}]</code>\n"
            f"   📁 {cat} | 📋 {qc} savol | 👁 {sc} marta | ⭐ {avg}%\n\n"
        )
        # Har test uchun knopkalar
        builder.row(
            InlineKeyboardButton(text=f"🔍 {title[:16]}", callback_data=f"mytest_view_{tid}"),
            InlineKeyboardButton(text="📤 Ulash",         callback_data=f"share_test_{tid}"),
            InlineKeyboardButton(text="📄 TXT",           callback_data=f"mytest_txt_{tid}"),
        )

    # Sahifa navigatsiyasi
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"mytests_p{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"mytests_p{page+1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))

    try:
        if edit: await msg.edit_text(text, reply_markup=builder.as_markup())
        else:    await msg.answer(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        await msg.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("mytest_view_"))
async def my_test_view(callback: CallbackQuery):
    """Test batafsil ma'lumoti va amallar"""
    await callback.answer()
    tid  = callback.data[12:]
    test = get_test(tid)
    if not test:
        return await callback.message.answer("❌ Test topilmadi.")

    from keyboards.keyboards import test_info_keyboard
    qs  = test.get("questions", [])
    vis = {"public": "🌍 Ommaviy", "link": "🔗 Ssilka", "private": "🔒 Shaxsiy"}.get(
        test.get("visibility"), "")
    diff_map = {"easy": "🟢 Oson", "medium": "🟡 O'rtacha",
                "hard": "🔴 Qiyin", "expert": "⚡ Ekspert"}
    diff = diff_map.get(test.get("difficulty", ""), "")

    text = (
        f"🔍 <b>TEST MA'LUMOTLARI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title')}</b>\n"
        f"📁 Fan: {test.get('category')}\n"
        f"📊 Qiyinlik: {diff}\n"
        f"📋 Savollar: <b>{len(qs)} ta</b>\n"
        f"🔒 Ko'rinish: {vis}\n"
        f"👁 Ishlangan: <b>{test.get('solve_count', 0)} marta</b>\n"
        f"⭐ O'rtacha: <b>{round(test.get('avg_score', 0), 1)}%</b>\n"
        f"🆔 Kod: <code>{tid}</code>"
    )
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="▶️ Inline test", callback_data=f"start_test_{tid}"),
        InlineKeyboardButton(text="📊 Poll test",   callback_data=f"start_poll_{tid}"),
    )
    builder.row(
        InlineKeyboardButton(text="📤 Ulashish",   callback_data=f"share_test_{tid}"),
        InlineKeyboardButton(text="📄 TXT yuklab", callback_data=f"mytest_txt_{tid}"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Reyting", callback_data=f"lb_test_{tid}"),
        InlineKeyboardButton(text="⬅️ Orqaga",  callback_data="mytests_p0"),
    )

    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("mytest_txt_"))
async def my_test_to_txt(callback: CallbackQuery):
    """Testni TXT formatda yuklab olish"""
    await callback.answer("⏳ TXT tayyorlanmoqda...")
    tid  = callback.data[11:]
    test = get_test(tid)
    if not test:
        return await callback.message.answer("❌ Test topilmadi.")

    txt = _test_to_txt(test, user=callback.from_user, bot_info=await callback.bot.me())
    doc = BufferedInputFile(txt.encode("utf-8"), filename=f"{test.get('title', tid)}.txt")
    await callback.message.answer_document(
        doc,
        caption=(
            f"📄 <b>{test.get('title')}</b> — TXT format\n"
            f"📋 {len(test.get('questions', []))} ta savol\n"
            f"🆔 Kod: <code>{tid}</code>"
        )
    )


@router.callback_query(F.data.startswith("share_test_"))
async def share_test(callback: CallbackQuery):
    """Testni ulashish ssilkasi"""
    await callback.answer()
    tid  = callback.data[11:]
    test = get_test(tid)
    if not test:
        return await callback.message.answer("❌ Test topilmadi.")

    bot_uname = (await callback.bot.me()).username
    link = f"https://t.me/{bot_uname}?start={tid}"

    text = (
        f"📤 <b>TEST ULASHISH</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 <b>{test.get('title')}</b>\n"
        f"📁 Fan: {test.get('category')}\n"
        f"📋 Savollar: {len(test.get('questions', []))} ta\n\n"
        f"🔑 Kod: <code>{tid}</code>\n"
        f"🔗 Ssilka:\n<code>{link}</code>\n\n"
        f"<i>💡 Ssilkani do'stlaringizga yuboring — ular ham ishlaydi!</i>"
    )
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"mytest_view_{tid}"))
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "go_tests")
async def go_tests(callback: CallbackQuery):
    await callback.answer()
    from handlers.tests import send_categories_menu
    await send_categories_menu(callback)


# ── YORDAMCHI: Test → TXT ─────────────────────────────────

def _test_to_txt(test: dict, user=None, bot_info=None) -> str:
    """Testni standart TXT formatga o'tkazish (user info + vaqt avtomatik)"""
    import datetime as _dt
    lines = []
    lines.append(f"# {test.get('title', 'Test')}")
    lines.append(f"# Fan: {test.get('category', '')}")
    lines.append(f"# Kod: {test.get('test_id', '')}")
    # Yaratuvchi ma'lumotlari
    if user:
        uname  = f"@{user.username}" if getattr(user, "username", None) else ""
        uname  = uname or f"id:{getattr(user, 'id', '')}"
        ufull  = getattr(user, "full_name", None) or getattr(user, "first_name", "")
        lines.append(f"# Yaratuvchi: {ufull} {uname}".strip())
    if bot_info:
        bname  = getattr(bot_info, "username", "")
        lines.append(f"# Bot: @{bname}")
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines.append(f"# Yuklab olindi: {now}")
    lines.append("")

    for i, q in enumerate(test.get("questions", []), 1):
        t = q.get("type", "multiple_choice")
        # TYPE yozilmaydi — sodda ko'rinish uchun
        lines.append(f"{i}. {q.get('question', q.get('text', ''))}")

        opts = q.get("options", [])
        corr = q.get("correct", "")

        if t in ("multiple_choice", "multi_select"):
            for opt in opts:
                opt_str = str(opt)
                if isinstance(corr, list):
                    marker = "===" if opt_str in corr else ""
                else:
                    is_c = False
                    import re
                    m1 = re.match(r"^([A-Za-z])", opt_str.strip())
                    m2 = re.match(r"^([A-Za-z])", str(corr).strip())
                    if m1 and m2:
                        is_c = m1.group(1).lower() == m2.group(1).lower()
                    else:
                        is_c = opt_str.strip() == str(corr).strip()
                    marker = "===" if is_c else ""
                lines.append(f"{marker}{opt_str}")
        elif t == "true_false":
            ans = "Ha" if "Ha" in str(corr) else "Yo'q"
            lines.append(f"Javob: {ans}")
        elif t in ("text_input", "fill_blank"):
            lines.append(f"Javob: {corr}")
            acc = q.get("accepted_answers", [])
            if acc:
                lines.append(f"Qabul_qilinadigan: {', '.join(acc)}")

        expl = q.get("explanation", "")
        if expl and expl not in ("Izoh kiritilmagan.", "Izoh yo'q", "Izoh kiritilmagan", ""):
            lines.append(f"Izoh: {expl}")
        lines.append("")

    return "\n".join(lines)
