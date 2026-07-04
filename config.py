import os

# ====== НАСТРОЙКИ ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "8568839501:AAE_JwGFuHpAwynjsC2enQIILi5Y0Dn4bio")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]

# ЮКасса
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "YOUR_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "YOUR_SECRET_KEY")

# Цена доступа (в рублях)
PRICE = 149

# Контакт для связи
CONTACT_USERNAME = "@Sunrg7j"
