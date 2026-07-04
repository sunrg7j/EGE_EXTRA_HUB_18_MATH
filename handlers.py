import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
import payment as pay
from keyboards import (
    main_menu, task_list_keyboard, task_keyboard,
    back_main, payment_keyboard, admin_keyboard,
    admin_task_type
)
from config import ADMIN_IDS, PRICE, CONTACT_USERNAME

router = Router()


# ==================== УТИЛИТЫ ====================

async def send_task(message_or_query, task, prefix: str, show_solution: bool = False):
    """Отправляет задачу (с картинкой если есть)"""
    bot: Bot = message_or_query.bot if hasattr(message_or_query, 'bot') else message_or_query.message.bot
    chat_id = message_or_query.chat.id if hasattr(message_or_query, 'chat') else message_or_query.message.chat.id

    # task = (id, title, description, image_path, solution, solution_image, is_demo, created_at)
    task_id, title, description, image_path, solution, solution_image, *_ = task

    caption = f"📌 <b>{title}</b>\n\n{description}"

    if show_solution:
        caption += f"\n\n{'─'*30}\n💡 <b>Разбор:</b>\n\n{solution}"
        img = solution_image
    else:
        img = image_path

    kb = task_keyboard(task_id, prefix) if not show_solution else back_main()

    if img and os.path.exists(img):
        photo = FSInputFile(img)
        await bot.send_photo(chat_id, photo, caption=caption, parse_mode="HTML", reply_markup=kb)
    else:
        await bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=kb)


# ==================== СТАРТ ====================

@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.get_or_create_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or ""
    )
    access = await db.has_access(message.from_user.id)
    name = message.from_user.first_name or "друг"
    text = (
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"Это курс по <b>Заданию №18 ЕГЭ по математике</b> — стереометрия и пространственные задачи.\n\n"
        f"🎯 Здесь ты найдёшь подробные разборы с картинками и пошаговым объяснением.\n\n"
        f"{'✅ У тебя есть полный доступ!' if access else f'💳 Полный доступ — всего <b>{PRICE}₽</b>'}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu(access))


# ==================== ГЛАВНОЕ МЕНЮ ====================

@router.callback_query(F.data == "back_main")
async def back_to_main(call: CallbackQuery):
    access = await db.has_access(call.from_user.id)
    await call.message.edit_text(
        "🏠 Главное меню — выбери раздел:",
        reply_markup=main_menu(access)
    )


@router.callback_query(F.data == "about")
async def about(call: CallbackQuery):
    text = (
        "📖 <b>О курсе</b>\n\n"
        "Задание №18 ЕГЭ — стереометрия. Многие сливают баллы именно здесь.\n\n"
        "В курсе:\n"
        "• Разборы реальных задач с картинками\n"
        "• Пошаговое объяснение хода мысли\n"
        "• Типовые приёмы и формулы\n"
        "• Задачи разного уровня сложности\n\n"
        f"💰 Цена полного доступа — <b>{PRICE}₽</b> (навсегда)"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_main())


@router.callback_query(F.data == "contact")
async def contact(call: CallbackQuery):
    text = (
        f"📩 <b>Связь с автором</b>\n\n"
        f"Есть вопросы по задачам или хочешь предложить тему?\n"
        f"Пиши: {CONTACT_USERNAME}\n\n"
        f"Отвечу в течение дня 👌"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_main())


# ==================== ДЕМО-ЗАДАЧИ ====================

@router.callback_query(F.data == "demo_list")
async def demo_list(call: CallbackQuery):
    tasks = await db.get_demo_tasks()
    await call.message.edit_text(
        "🆓 <b>Бесплатные демо-задачи</b>\n\nВыбери задачу для разбора:",
        parse_mode="HTML",
        reply_markup=task_list_keyboard(tasks, "demo")
    )


@router.callback_query(F.data.startswith("demo_") & ~F.data.startswith("demo_list"))
async def demo_task(call: CallbackQuery):
    task_id = int(call.data.split("_")[1])
    task = await db.get_task(task_id)
    if not task:
        await call.answer("Задача не найдена", show_alert=True)
        return
    await call.message.delete()
    await send_task(call.message, task, "demo")


@router.callback_query(F.data.startswith("solution_demo_"))
async def demo_solution(call: CallbackQuery):
    task_id = int(call.data.split("_")[2])
    task = await db.get_task(task_id)
    await call.message.delete()
    await send_task(call.message, task, "demo", show_solution=True)


# ==================== ВСЕ ЗАДАЧИ (платные) ====================

@router.callback_query(F.data == "all_tasks")
async def all_tasks(call: CallbackQuery):
    if not await db.has_access(call.from_user.id):
        await call.answer("⛔ Нужен полный доступ!", show_alert=True)
        return
    tasks = await db.get_all_tasks()
    await call.message.edit_text(
        "📚 <b>Все задачи курса</b>\n\nВыбери задачу:",
        parse_mode="HTML",
        reply_markup=task_list_keyboard(tasks, "task")
    )


@router.callback_query(F.data.startswith("task_") & ~F.data.startswith("task_list"))
async def paid_task(call: CallbackQuery):
    if not await db.has_access(call.from_user.id):
        await call.answer("⛔ Нужен полный доступ!", show_alert=True)
        return
    task_id = int(call.data.split("_")[1])
    task = await db.get_task(task_id)
    if not task:
        await call.answer("Задача не найдена", show_alert=True)
        return
    await call.message.delete()
    await send_task(call.message, task, "task")


@router.callback_query(F.data.startswith("solution_task_"))
async def paid_solution(call: CallbackQuery):
    if not await db.has_access(call.from_user.id):
        await call.answer("⛔ Нужен полный доступ!", show_alert=True)
        return
    task_id = int(call.data.split("_")[2])
    task = await db.get_task(task_id)
    await call.message.delete()
    await send_task(call.message, task, "task", show_solution=True)


# ==================== ОПЛАТА ====================

# Хранилище ожидающих платежей: {user_id: payment_id}
pending_payments: dict[int, str] = {}


@router.callback_query(F.data == "buy")
async def buy(call: CallbackQuery):
    user_id = call.from_user.id

    if await db.has_access(user_id):
        await call.answer("✅ У тебя уже есть доступ!", show_alert=True)
        return

    try:
        payment_id, url = await pay.create_payment(user_id)
        await db.create_payment(user_id, payment_id, PRICE)
        pending_payments[user_id] = payment_id

        text = (
            f"💳 <b>Оплата полного доступа</b>\n\n"
            f"Цена: <b>{PRICE}₽</b>\n"
            f"Доступны: карта, СБП, ЮMoney и другие\n\n"
            f"После оплаты нажми кнопку <b>«Я оплатил — проверить»</b> ⬇️"
        )
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=payment_keyboard(url))
    except Exception as e:
        await call.message.edit_text(
            "⚠️ Ошибка при создании платежа. Напиши нам — поможем!\n"
            f"{CONTACT_USERNAME}",
            reply_markup=back_main()
        )


@router.callback_query(F.data == "check_payment")
async def check_payment(call: CallbackQuery):
    user_id = call.from_user.id
    payment_id = pending_payments.get(user_id)

    if not payment_id:
        await call.answer("Платёж не найден. Попробуй купить снова.", show_alert=True)
        return

    status = await pay.check_payment_status(payment_id)

    if status == "succeeded":
        await db.confirm_payment(payment_id)
        await db.grant_access(user_id)
        pending_payments.pop(user_id, None)
        await call.message.edit_text(
            "🎉 <b>Оплата прошла! Добро пожаловать!</b>\n\n"
            "Теперь у тебя есть доступ ко всем задачам курса 🚀",
            parse_mode="HTML",
            reply_markup=main_menu(True)
        )
    elif status == "canceled":
        await call.message.edit_text(
            "❌ Платёж отменён. Попробуй снова.",
            reply_markup=back_main()
        )
    else:
        await call.answer("⏳ Платёж ещё не поступил. Подожди немного и попробуй снова.", show_alert=True)


# ==================== АДМИН-ПАНЕЛЬ ====================

class AddTask(StatesGroup):
    waiting_type = State()
    waiting_title = State()
    waiting_description = State()
    waiting_image = State()
    waiting_solution = State()
    waiting_solution_image = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    users, paid, revenue, tasks = await db.get_stats()
    text = (
        f"🛠 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"💳 С доступом: <b>{paid}</b>\n"
        f"💰 Выручка: <b>{revenue}₽</b>\n"
        f"📚 Задач в базе: <b>{tasks}</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    users, paid, revenue, tasks = await db.get_stats()
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"💳 С доступом: <b>{paid}</b>\n"
        f"💰 Выручка: <b>{revenue}₽</b>\n"
        f"📚 Задач в базе: <b>{tasks}</b>"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin_add")
async def admin_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "Какой тип задачи?",
        reply_markup=admin_task_type()
    )
    await state.set_state(AddTask.waiting_type)


@router.callback_query(F.data.in_(["tasktype_demo", "tasktype_paid"]), AddTask.waiting_type)
async def admin_task_type_chosen(call: CallbackQuery, state: FSMContext):
    is_demo = 1 if call.data == "tasktype_demo" else 0
    await state.update_data(is_demo=is_demo)
    await call.message.edit_text("✏️ Введи <b>название</b> задачи:", parse_mode="HTML")
    await state.set_state(AddTask.waiting_title)


@router.message(AddTask.waiting_title)
async def admin_got_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Введи <b>условие задачи</b> (текст):", parse_mode="HTML")
    await state.set_state(AddTask.waiting_description)


@router.message(AddTask.waiting_description)
async def admin_got_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "🖼 Отправь <b>картинку условия</b> или напиши <code>нет</code> если её нет:",
        parse_mode="HTML"
    )
    await state.set_state(AddTask.waiting_image)


@router.message(AddTask.waiting_image, F.photo)
async def admin_got_image(message: Message, state: FSMContext, bot: Bot):
    os.makedirs("images", exist_ok=True)
    photo = message.photo[-1]
    path = f"images/task_{photo.file_id}.jpg"
    await bot.download(photo, destination=path)
    await state.update_data(image_path=path)
    await message.answer("💡 Введи <b>текст разбора</b>:", parse_mode="HTML")
    await state.set_state(AddTask.waiting_solution)


@router.message(AddTask.waiting_image)
async def admin_no_image(message: Message, state: FSMContext):
    await state.update_data(image_path=None)
    await message.answer("💡 Введи <b>текст разбора</b>:", parse_mode="HTML")
    await state.set_state(AddTask.waiting_solution)


@router.message(AddTask.waiting_solution)
async def admin_got_solution(message: Message, state: FSMContext):
    await state.update_data(solution=message.text)
    await message.answer(
        "🖼 Отправь <b>картинку разбора</b> или напиши <code>нет</code>:",
        parse_mode="HTML"
    )
    await state.set_state(AddTask.waiting_solution_image)


@router.message(AddTask.waiting_solution_image, F.photo)
async def admin_got_solution_image(message: Message, state: FSMContext, bot: Bot):
    os.makedirs("images", exist_ok=True)
    photo = message.photo[-1]
    path = f"images/solution_{photo.file_id}.jpg"
    await bot.download(photo, destination=path)
    await state.update_data(solution_image=path)
    await finish_add_task(message, state)


@router.message(AddTask.waiting_solution_image)
async def admin_no_solution_image(message: Message, state: FSMContext):
    await state.update_data(solution_image=None)
    await finish_add_task(message, state)


async def finish_add_task(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_task(
        title=data["title"],
        description=data["description"],
        image_path=data.get("image_path"),
        solution=data["solution"],
        solution_image=data.get("solution_image"),
        is_demo=data.get("is_demo", 0)
    )
    await state.clear()
    await message.answer(
        "✅ <b>Задача добавлена!</b>",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )
