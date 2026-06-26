import datetime
import pytz
from config import FREE_REQUESTS_PER_WEEK, ADMINS
from database import get_user

MOSCOW_TZ = pytz.timezone("Europe/Moscow")

def get_week_start() -> str:
    now = datetime.datetime.now(MOSCOW_TZ)
    start = now - datetime.timedelta(days=now.weekday())
    return start.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def has_active_subscription(user_data: dict) -> bool:
    end = user_data.get("subscription_end")
    if not end:
        return False
    try:
        end_date = datetime.datetime.fromisoformat(end)
        return datetime.datetime.now(MOSCOW_TZ) < end_date
    except:
        return False

def can_send_message(user_id: int, user_data: dict) -> bool:
    if is_admin(user_id):
        return True
    if has_active_subscription(user_data):
        return True
    week_start = user_data.get("week_start")
    current = get_week_start()
    if week_start != current:
        user_data["week_start"] = current
        user_data["free_used_week"] = 0
    return user_data.get("free_used_week", 0) < FREE_REQUESTS_PER_WEEK

def increment_used(user_data: dict):
    if has_active_subscription(user_data):
        return
    user_data["free_used_week"] = user_data.get("free_used_week", 0) + 1

def get_remaining_requests(user_id: int) -> str:
    user = get_user(user_id)
    if not user:
        return str(FREE_REQUESTS_PER_WEEK)
    if is_admin(user_id):
        return "∞ (администратор)"
    if has_active_subscription(user):
        return "∞ (безлимит по подписке)"
    week_start = user.get("week_start")
    current = get_week_start()
    if week_start != current:
        user["week_start"] = current
        user["free_used_week"] = 0
        # сохранять не обязательно, но можно сделать save_user(user) если импортировать
    used = user.get("free_used_week", 0)
    remaining = FREE_REQUESTS_PER_WEEK - used
    return str(remaining if remaining > 0 else 0)