import uuid
import aiohttp
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, PRICE


YOOKASSA_URL = "https://api.yookassa.ru/v3/payments"


async def create_payment(user_id: int) -> tuple[str, str]:
    """
    Создаёт платёж в ЮКассе.
    Возвращает (payment_id, confirmation_url)
    СБП автоматически доступен как метод оплаты.
    """
    idempotency_key = str(uuid.uuid4())
    payload = {
        "amount": {
            "value": f"{PRICE}.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/your_bot"  # замени на @username бота
        },
        "capture": True,
        "description": f"Полный доступ к курсу №18 ЕГЭ | user {user_id}",
        "metadata": {
            "user_id": str(user_id)
        },
        "payment_method_data": {
            # убираем — тогда ЮКасса сама предложит все методы включая СБП
        }
    }
    # Убираем пустой payment_method_data
    del payload["payment_method_data"]

    auth = aiohttp.BasicAuth(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
    headers = {
        "Idempotence-Key": idempotency_key,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(YOOKASSA_URL, json=payload, auth=auth, headers=headers) as resp:
            data = await resp.json()

    payment_id = data["id"]
    confirmation_url = data["confirmation"]["confirmation_url"]
    return payment_id, confirmation_url


async def check_payment_status(payment_id: str) -> str:
    """Проверяет статус платежа. Возвращает 'succeeded', 'pending', 'canceled'"""
    auth = aiohttp.BasicAuth(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{YOOKASSA_URL}/{payment_id}", auth=auth) as resp:
            data = await resp.json()

    return data.get("status", "pending")
