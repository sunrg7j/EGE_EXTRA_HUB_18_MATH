from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu(has_access: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📚 Демо-задачи (бесплатно)", callback_data="demo_list")],
    ]
    if has_access:
        buttons.append([InlineKeyboardButton(text="🔓 Все задачи", callback_data="all_tasks")])
    else:
        buttons.append([InlineKeyboardButton(text="💳 Купить полный доступ", callback_data="buy")])
    buttons += [
        [InlineKeyboardButton(text="ℹ️ О курсе", callback_data="about")],
        [InlineKeyboardButton(text="📩 Связаться", callback_data="contact")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_list_keyboard(tasks: list, prefix: str) -> InlineKeyboardMarkup:
    """tasks = [(id, title), ...]"""
    buttons = [
        [InlineKeyboardButton(text=f"📝 {title}", callback_data=f"{prefix}_{task_id}")]
        for task_id, title in tasks
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_keyboard(task_id: int, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Показать разбор", callback_data=f"solution_{prefix}_{task_id}")],
        [InlineKeyboardButton(text="🔙 К списку задач", callback_data=f"{prefix}_list")],
    ])


def back_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_main")]
    ])


def payment_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=url)],
        [InlineKeyboardButton(text="✅ Я оплатил — проверить", callback_data="check_payment")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")],
    ])


# Админ-панель
def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="admin_add")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="back_main")],
    ])


def admin_task_type() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Демо (бесплатная)", callback_data="tasktype_demo")],
        [InlineKeyboardButton(text="💰 Платная", callback_data="tasktype_paid")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="back_main")],
    ])
