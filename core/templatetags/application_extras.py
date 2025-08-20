# core/templatetags/application_extras.py

import json
from django import template
from datetime import datetime

register = template.Library()

@register.filter
def parse_guests(guests_json):
    try:
        guests = json.loads(guests_json)
    except Exception:
        return [{"fio": "Ошибка: некорректные данные", "relationship": "", "birthdate": ""}]
    result = []
    for g in guests:
        fio = f"{g.get('last_name', '')} {g.get('first_name', '')} {g.get('patronymic', '')}".strip()
        rel = g.get('relationship', '')
        bd = g.get('birthdate', '')
        # Преобразуем к date если возможно
        birthdate_obj = None
        if bd:
            try:
                birthdate_obj = datetime.strptime(bd, "%Y-%m-%d").date()
            except Exception:
                birthdate_obj = bd  # fallback to raw string
        result.append({
            "fio": fio,
            "relationship": rel,
            "birthdate": birthdate_obj,
        })
    return result


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '-')

