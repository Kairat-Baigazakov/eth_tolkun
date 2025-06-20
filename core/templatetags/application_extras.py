# core/templatetags/application_extras.py

import json
from django import template

register = template.Library()

@register.filter
def parse_guests(guests_json):
    try:
        guests = json.loads(guests_json)
    except Exception:
        return ["Ошибка: некорректные данные"]
    result = []
    for g in guests:
        fio = f"{g.get('last_name', '')} {g.get('first_name', '')} {g.get('patronymic', '')}"
        rel = g.get('relationship', '')
        bd = g.get('birthdate', '')
        result.append(f"{fio.strip()} ({rel}, {bd})")
    return result


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '-')

