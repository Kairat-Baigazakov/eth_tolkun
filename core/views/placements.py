from django.shortcuts import render, get_object_or_404
from core.decorators import admin_or_moderator_required
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.safestring import mark_safe
from ..models import Arrival, Application, RoomLayout, RoomPlacement
import json

@login_required
@admin_or_moderator_required
def placement_page(request):
    arrival_id = request.GET.get("arrival", "")
    building_type = request.GET.get("building_type", "")
    floor = request.GET.get("floor", "")

    arrivals = Arrival.objects.order_by("-start_date")
    building_types = RoomLayout.objects.values_list("building_type", flat=True).distinct()
    floors = []
    rooms = []
    placements = []
    available_guests = []
    approved_apps = []

    if arrival_id and building_type and floor:
        rooms = RoomLayout.objects.filter(building_type=building_type, floor=floor)
        placements = RoomPlacement.objects.filter(arrival_id=arrival_id, room__in=rooms).select_related("room", "application")
        # Список гостей из approved заявок, которых еще не разместили
        approved_apps = Application.objects.filter(arrival_id=arrival_id, status="approved")
        placed_fios = set(p.guest_fio for p in placements)
        for app in approved_apps:
            guests = []
            try:
                guests = json.loads(app.guests or "[]")
            except Exception:
                pass
            for g in guests:
                fio = " ".join([g.get("last_name", ""), g.get("first_name", ""), g.get("patronymic", "")]).strip()
                if fio and fio not in placed_fios:
                    available_guests.append({
                        "fio": fio,
                        "app_id": app.id,
                        "app": app,
                    })

    # Floors by building_type
    if building_type:
        floors = RoomLayout.objects.filter(building_type=building_type).values_list("floor", flat=True).distinct().order_by("floor")
    else:
        floors = RoomLayout.objects.values_list("floor", flat=True).distinct().order_by("floor")

    room_placements_map = {}  # room.id -> список guest_fio (размером с room.capacity)
    for room in rooms:
        # Список гостей в этой комнате
        placements_in_room = [p.guest_fio for p in placements if p.room_id == room.id]
        # Если мест больше чем гостей, дополним пустыми строками
        placements_for_fields = placements_in_room + [""] * (room.capacity - len(placements_in_room))
        placements_for_fields = placements_for_fields[:room.capacity]  # На всякий случай обрежем
        room_placements_map[room.id] = placements_for_fields

    rooms_json = []
    for room in rooms:
        rooms_json.append({
            "id": room.id,
            "name": room.name,
            "capacity": room.capacity,
            "placements": room_placements_map.get(room.id, []),
        })

    # Готовим гостей для JS
    available_guests_json = [
        {
            "fio": g["fio"],
            "application_id": g["app_id"]
        }
        for g in available_guests
    ]

    all_guests_json = [
        {
            "fio": fio,  # то же что и в placements/placements_for_fields
            "application_id": app.id
        }
        for app in approved_apps
        for g in (json.loads(app.guests or "[]"))
        for fio in [" ".join([g.get("last_name", ""), g.get("first_name", ""), g.get("patronymic", "")]).strip()]
    ]

    context = {
        "room_placements_map": room_placements_map,
        "rooms_json": mark_safe(json.dumps(rooms_json, cls=DjangoJSONEncoder)),
        "available_guests_json": mark_safe(json.dumps(available_guests_json, cls=DjangoJSONEncoder)),
        "all_guests_json": mark_safe(json.dumps(all_guests_json, cls=DjangoJSONEncoder)),
        "arrivals": arrivals,
        "arrival_id": arrival_id,
        "building_types": building_types,
        "building_type": building_type,
        "floors": floors,
        "floor": floor,
        "rooms": rooms,
        "placements": placements,
        "available_guests": available_guests,
    }
    return render(request, "placements/placement_page.html", context)


@login_required
@admin_or_moderator_required
@require_POST
def save_placements(request):
    import json
    data = json.loads(request.body)
    room_id = data.get('room_id')
    guest_fios = data.get('guest_fios', [])
    arrival_id = data.get('arrival_id') or request.GET.get('arrival') or request.POST.get('arrival_id')

    room = get_object_or_404(RoomLayout, id=room_id)

    # Удаляем старые размещения для этой комнаты и этого заезда
    RoomPlacement.objects.filter(room_id=room_id, arrival_id=arrival_id).delete()

    guest_fios_unique = []
    seen = set()
    for fio in guest_fios:
        fio_clean = fio.strip()
        if fio_clean and fio_clean not in seen:
            guest_fios_unique.append(fio_clean)
            seen.add(fio_clean)

    failed = []
    approved_apps = Application.objects.filter(arrival_id=arrival_id, status="approved")

    for fio_clean in guest_fios_unique:
        fio_clean = fio_clean.strip()
        if not fio_clean:
            continue

        found_app = None
        for app in approved_apps:
            try:
                guests = json.loads(app.guests or "[]")
            except Exception as ex:
                continue

            for g in guests:
                guest_fio = " ".join([
                    g.get("last_name", "").strip(),
                    g.get("first_name", "").strip(),
                    g.get("patronymic", "").strip()
                ]).strip()
                if guest_fio.lower() == fio_clean.lower():
                    found_app = app
                    break
            if found_app:
                break

        if found_app:
            RoomPlacement.objects.create(
                arrival_id=arrival_id,
                room_id=room_id,
                application=found_app,
                guest_fio=fio_clean
            )
            found_app.check_guests_placemented()
        else:
            failed.append(fio_clean)

    if failed:
        return JsonResponse({'success': False, 'not_found': failed})
    return JsonResponse({'success': True})


@login_required
@admin_or_moderator_required
@require_POST
def assign_rooms(request):
    arrival_id = request.GET.get("arrival")
    building_type = request.GET.get("building_type")
    floor = request.GET.get("floor")

    # 1. Получаем все размещения в этом заезде/корпусе/этаже
    placements = RoomPlacement.objects.filter(
        arrival_id=arrival_id,
        room__building_type=building_type,
        room__floor=floor,
    ).select_related("room", "application")

    # 2. Собираем {application_id: [названия комнат]}
    app_rooms = {}
    for p in placements:
        key = p.application_id
        value = f"{p.room.name}, {p.room.building_type}"
        app_rooms.setdefault(key, set()).add(value)

    # 3. Обновляем заявки
    for app_id, rooms in app_rooms.items():
        app = Application.objects.get(id=app_id)
        # Сохраним комнаты как строку через запятую
        app.rooms = "; ".join(rooms)
        app.save(update_fields=['rooms'])

    return JsonResponse({'success': True})
