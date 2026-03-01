"""
👤 PROFIL, NATIJALAR VA MENING TESTLARIM
- Natijalarim → history.html WebApp (Firebase ma'lumotlari)
- Tahlilim → review.html WebApp (oxirgi natija)
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.exceptions import TelegramBadRequest

from firebase.db import get_user, get_user_results, get_test, get_my_tests
from keyboards.keyboards import main_reply_keyboard, _webapp_url

log = logging.getLogger(__name__)
router = Router()

PAGE_SIZE_RESULTS = 8
PAGE_SIZE_TESTS = 5


# ══════════════════════════════════════════════════════════
# PROFIL
# ══════════════════════════════════════════════════════════

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
    avg = round(user.get("avg_score", 0), 1)
    total = user.get("total_tests", 0)

    badges = []
    if total >= 1:  badges.append("🥉 Boshliqchi")
    if total >= 10: badges.append("🥈 Tajribali")
    if total >= 50: badges.append("🥇 Ustoz")
    if avg >= 90:   badges.append("🌟 Mukammal")
    if avg >= 80:   badges.append("🔥 A'lochi")
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
    builder.row(InlineKeyboardButton(text="📊 Natijalarim tarixi", callback_data="results_p0"))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu"))
    kb = builder.as_markup()
    try:
        if edit:
            await msg.edit_text(text, reply_markup=kb)
        else:
            await msg.answer(text, reply_markup=kb)
    except TelegramBadRequest:
        await msg.answer(text, reply_markup=kb)


# ══════════════════════════════════════════════════════════
# NATIJALARIM
# ══════════════════════════════════════════════════════════

@router.message(F.text == "📊 Natijalarim")
async def results_msg(message: Message):
    uid = message.from_user.id
    results = get_user_results(uid, limit=200)

    if not results:
        return await message.answer(
            "📭 <b>Hali test yechmagansiz.</b>\n\nTestlar bo'limiga o'ting!",
            reply_markup=main_reply_keyboard(uid)
        )

    builder = InlineKeyboardBuilder()

    # WebApp — history.html orqali ko'rish
    url = _webapp_url("history.html", results[:50])
    if url:
        builder.row(InlineKeyboardButton(
            text="📜 Barcha natijalar (Web App)",
            web_app=WebAppInfo(url=url)
        ))

    builder.row(InlineKeyboardButton(
        text="📋 Ro'yxat ko'rinishi", callback_data="results_p0"
    ))
    builder.row(InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu"))

    # Qisqacha statistika
    total = len(results)
    avg = round(sum(r.get("percentage", 0) for r in results) / total, 1) if total else 0
    passed = sum(1 for r in results if r.get("passed"))

    await message.answer(
        f"📊 <b>NATIJALARIM</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 Jami: <b>{total} ta</b> test\n"
        f"✅ O'tgan: <b>{passed} ta</b>\n"
        f"📈 O'rtacha: <b>{avg}%</b>\n\n"
        f"<i>Web App orqali batafsil ko'rish:</i>",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("results_p"))
async def results_page(callback: CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    page = int(callback.data[9:])
    results = get_user_results(uid, limit=200)

    if not results:
        try:
            await callback.message.edit_text("📭 Hali natijalar yo'q.")
        except TelegramBadRequest:
            pass
        return

    start = page * PAGE_SIZE_RESULTS
    chunk = results[start: start + PAGE_SIZE_RESULTS]
    total = len(results)
    pages = (total - 1) // PAGE_SIZE_RESULTS

    lines = [f"📊 <b>NATIJALARIM</b> (sahifa {page + 1}/{pages + 1})\n━━━━━━━━━━━━━━━━━━━━━━\n"]
    for i, r in enumerate(chunk, start=start + 1):
        pct = r.get("percentage", 0)
        icon = "✅" if r.get("passed") else "❌"
        test_id = r.get("test_id", "")
        # Test nomini topish
        t = get_test(test_id)
        t_name = t.get("title", test_id)[:25] if t else test_id[:25]
        dt = r.get("completed_at", "")[:10]
        lines.append(f"{icon} <b>{i}.</b> {t_name} — <b>{pct}%</b> <i>({dt})</i>")

    text = "\n".join(lines)
    builder = InlineKeyboardBuilder()

    # Tahlil tugmalari
    for r in chunk:
        rid = r.get("result_id", "")
        test_id = r.get("test_id", "")
        t = get_test(test_id)
        t_name = (t.get("title", test_id)[:15] if t else test_id[:15])
        if rid:
            builder.row(InlineKeyboardButton(
                text=f"🔍 {t_name} tahlili",
                callback_data=f"analysis_{rid}"
            ))

    # Sahifalash
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"results_p{page - 1}"))
    if page < pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"results_p{page + 1}"))
    if nav:
        builder.row(*nav)

    # WebApp tarixi
    url = _webapp_url("history.html", results[:50])
    if url:
        builder.row(InlineKeyboardButton(
            text="📜 Web App tarix",
            web_app=WebAppInfo(url=url)
        ))

    builder.row(InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu"))
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("analysis_"))
async def analysis_cb(callback: CallbackQuery):
    await callback.answer()
    rid = callback.data[9:]
    from firebase.db import get_result_by_id
    result = get_result_by_id(rid)
    if not result:
        return await callback.answer("❌ Natija topilmadi", show_alert=True)

    test_id = result.get("test_id", "")
    t = get_test(test_id)
    t_name = t.get("title", test_id) if t else test_id

    pct = result.get("percentage", 0)
    passed = result.get("passed", False)
    correct = result.get("correct_count", 0)
    total = result.get("total_questions", 0)
    elapsed = result.get("time_spent", 0)
    m, s = divmod(elapsed, 60)
    icon = "🏆" if passed else "😔"
    bar_len = 10
    filled = round(pct / 100 * bar_len)
    bar = "🟩" * filled + "🟥" * (bar_len - filled)

    text = (
        f"{icon} <b>{t_name.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{bar}  <b>{pct}%</b>\n\n"
        f"✅ To'g'ri: <b>{correct}</b> ta\n"
        f"❌ Xato: <b>{total - correct}</b> ta\n"
        f"📋 Jami: <b>{total}</b> ta\n"
        f"⏱ Vaqt: <b>{m}:{s:02d}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{'✅ O\'TDINGIZ!' if passed else '❌ O\'TMADINGIZ'}"
    )

    builder = InlineKeyboardBuilder()

    # Web App tahlil
    review_data = {
        "title": t_name,
        "score": pct, "correct": correct, "total": total,
        "passed": passed, "elapsed": elapsed,
        "questions": result.get("detailed_results", []),
    }
    from keyboards.keyboards import _webapp_url
    url = _webapp_url("review.html", review_data)
    if url:
        builder.row(InlineKeyboardButton(
            text="🔍 Batafsil tahlil (Web App)",
            web_app=WebAppInfo(url=url)
        ))

    builder.row(
        InlineKeyboardButton(text="🔄 Qaytadan", callback_data=f"start_test_{test_id}"),
        InlineKeyboardButton(text="📊 Poll", callback_data=f"start_poll_{test_id}"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="results_p0"))

    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=builder.as_markup())


# ══════════════════════════════════════════════════════════
# MENING TESTLARIM
# ══════════════════════════════════════════════════════════

@router.message(F.text == "🗂 Mening testlarim")
async def my_tests_msg(message: Message):
    uid = message.from_user.id
    tests = get_my_tests(uid)
    if not tests:
        return await message.answer(
            "📭 <b>Siz hali test yaratmagansiz.</b>\n\n"
            "➕ Test Yaratish tugmasini bosing!",
            reply_markup=main_reply_keyboard(uid)
        )
    await _show_my_tests(message, uid, tests, page=0, is_callback=False)


@router.callback_query(F.data.startswith("mytests_p"))
async def my_tests_page(callback: CallbackQuery):
    await callback.answer()
    uid = callback.from_user.id
    page = int(callback.data[9:])
    tests = get_my_tests(uid)
    await _show_my_tests(callback.message, uid, tests, page=page, is_callback=True)


async def _show_my_tests(msg, uid: int, tests: list, page: int, is_callback: bool):
    start = page * PAGE_SIZE_TESTS
    chunk = tests[start: start + PAGE_SIZE_TESTS]
    total = len(tests)
    pages = (total - 1) // PAGE_SIZE_TESTS

    text = f"🗂 <b>MENING TESTLARIM</b> ({page + 1}/{pages + 1})\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for t in chunk:
        qc = len(t.get("questions", []))
        vis_map = {"public": "🌍", "link": "🔗", "private": "🔒"}
        vis = vis_map.get(t.get("visibility", ""), "")
        text += (
            f"{vis} <b>{t.get('title', 'Nomsiz')}</b>\n"
            f"   📁 {t.get('category', '')} | 📋 {qc} ta | 🆔 <code>{t.get('test_id')}</code>\n\n"
        )

    builder = InlineKeyboardBuilder()
    for t in chunk:
        tid = t.get("test_id", "")
        builder.row(
            InlineKeyboardButton(text=f"📝 {t.get('title', tid)[:20]}", callback_data=f"view_test_{tid}"),
            InlineKeyboardButton(text="📄 TXT", callback_data=f"dl_test_{tid}"),
            InlineKeyboardButton(text="🗑", callback_data=f"del_test_{tid}"),
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"mytests_p{page - 1}"))
    if page < pages:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"mytests_p{page + 1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🏠 Asosiy", callback_data="main_menu"))

    try:
        if is_callback:
            await msg.edit_text(text, reply_markup=builder.as_markup())
        else:
            await msg.answer(text, reply_markup=builder.as_markup())
    except TelegramBadRequest:
        await msg.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("dl_test_"))
async def download_test(callback: CallbackQuery):
    await callback.answer("⏳ Tayyorlanmoqda...")
    tid = callback.data[8:]
    test = get_test(tid)
    if not test:
        return await callback.answer("❌ Test topilmadi", show_alert=True)
    txt = _test_to_txt(test)
    doc = BufferedInputFile(txt.encode("utf-8"), filename=f"{test.get('title', tid)}.txt")
    await callback.message.answer_document(
        doc, caption=f"📄 <b>{test.get('title', tid)}</b>\n📋 {len(test.get('questions', []))} ta savol"
    )


@router.callback_query(F.data.startswith("del_test_"))
async def delete_test_cb(callback: CallbackQuery):
    tid = callback.data[9:]
    test = get_test(tid)
    if not test:
        return await callback.answer("❌ Topilmadi", show_alert=True)
    if test.get("creator_id") != callback.from_user.id:
        return await callback.answer("🚫 Bu sizning testingiz emas!", show_alert=True)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_del_{tid}"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="mytests_p0"),
    )
    try:
        await callback.message.edit_text(
            f"🗑 <b>{test.get('title', tid)}</b> ni o'chirishni tasdiqlaysizmi?",
            reply_markup=builder.as_markup()
        )
    except TelegramBadRequest:
        pass


@router.callback_query(F.data.startswith("confirm_del_"))
async def confirm_delete(callback: CallbackQuery):
    await callback.answer()
    tid = callback.data[12:]
    from firebase.db import delete_test
    delete_test(tid)
    await callback.message.edit_text("✅ Test o'chirildi!")
    import asyncio
    await asyncio.sleep(1.5)
    uid = callback.from_user.id
    tests = get_my_tests(uid)
    await _show_my_tests(callback.message, uid, tests, page=0, is_callback=True)


@router.callback_query(F.data.startswith("share_test_"))
async def share_test(callback: CallbackQuery):
    await callback.answer()
    tid = callback.data[11:]
    bot_user = await callback.bot.me()
    link = f"https://t.me/{bot_user.username}?start={tid}"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="mytests_p0"))
    try:
        await callback.message.edit_text(
            f"🔗 <b>TEST HAVOLASI</b>\n\n"
            f"Kod: <code>{tid}</code>\n"
            f"Link: <code>{link}</code>\n\n"
            f"<i>Ushbu havolani do'stlaringizga yuboring!</i>",
            reply_markup=builder.as_markup()
        )
    except TelegramBadRequest:
        pass


def _test_to_txt(test: dict, user=None, bot_info=None) -> str:
    """Testni TXT formatga o'tkazish"""
    lines = []
    title = test.get("title", "Test")
    cat = test.get("category", "Boshqa")
    tid = test.get("test_id", "")
    lines.append(f"# {title}")
    lines.append(f"# Fan: {cat} | ID: {tid}")
    lines.append("")

    LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    for i, q in enumerate(test.get("questions", []), 1):
        qtype = q.get("type", "multiple_choice")
        q_text = q.get("question") or q.get("text", "")
        expl = q.get("explanation", "")

        if qtype in ("multiple_choice",):
            lines.append(f"{i}. {q_text}")
            opts = q.get("options", [])
            correct = q.get("correct", 0)
            for j, opt in enumerate(opts):
                ot = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
                is_correct = (j == correct) if isinstance(correct, int) else False
                prefix = "===" if is_correct else ""
                lines.append(f"{prefix}{LETTERS[j]}) {ot}")
            if expl:
                lines.append(f"Izoh: {expl}")
        elif qtype == "true_false":
            lines.append(f"TYPE: true_false")
            lines.append(f"{i}. {q_text}")
            correct = q.get("correct", "Ha")
            lines.append(f"Javob: {correct}")
            if expl:
                lines.append(f"Izoh: {expl}")
        elif qtype in ("fill_blank", "text_input"):
            lines.append(f"TYPE: fill_blank")
            lines.append(f"{i}. {q_text}")
            ans = q.get("correctAnswer") or q.get("correct_answer", "")
            lines.append(f"Javob: {ans}")
            if expl:
                lines.append(f"Izoh: {expl}")
        elif qtype in ("matching", "match"):
            lines.append(f"TYPE: matching")
            lines.append(f"{i}. {q_text}")
            for pair in q.get("pairs", []):
                lines.append(f"Chap: {pair.get('left', '')} | {pair.get('right', '')}")
        elif qtype in ("ordering", "order"):
            lines.append(f"TYPE: ordering")
            lines.append(f"{i}. {q_text}")
            for wi, word in enumerate(q.get("words") or q.get("items", []), 1):
                lines.append(f"{wi}. {word}")
        elif qtype == "multi_select":
            lines.append(f"TYPE: multi_select")
            lines.append(f"{i}. {q_text}")
            opts = q.get("options", [])
            correct_list = q.get("correct", [])
            if isinstance(correct_list, int):
                correct_list = [correct_list]
            for j, opt in enumerate(opts):
                ot = str(opt).split(")", 1)[-1].strip() if ")" in str(opt) else str(opt)
                is_correct = j in correct_list
                prefix = "===" if is_correct else ""
                lines.append(f"{prefix}{LETTERS[j]}) {ot}")
            if expl:
                lines.append(f"Izoh: {expl}")
        else:
            lines.append(f"{i}. {q_text}")

        lines.append("")

    return "\n".join(lines)
