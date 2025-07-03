import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Arrival, Rate, RoomLayout, RoomPlacement, Application, Relative
from .forms import LoginForm, UserCreationForm, UserEditForm, ArrivalForm, RateForm, RoomLayoutForm, ApplicationForm, RelativeForm, ApplicationEditForm
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe

User = get_user_model()


# Вход и Выход  --------------------------------------------------------------------------------------------------------------------------------------------------
class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'login.html'

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'role'):
            if user.role == 'admin':
                return reverse_lazy('admin_dashboard')
            elif user.role == 'moderator':
                return reverse_lazy('moderator_dashboard')
            else:
                return reverse_lazy('user_dashboard')
        else:
            # Роль не задана, направим на user_dashboard или logout
            return reverse_lazy('user_dashboard')


def index(request):
    return redirect('login')


def logout_view(request):
    logout(request)
    return redirect('login')

# Проверки --------------------------------------------------------------------------------------------------------------------------------------------------
def admin_check(user):
    return user.is_authenticated and user.role == 'admin'


def admin_or_moderator(user):
    return user.is_authenticated and user.role in ['admin', 'moderator']

# ПОЛЬЗОВАТЕЛИ  --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
@user_passes_test(admin_check)
def user_create(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'admin/user/user_create.html', {'form': form})


@login_required
@user_passes_test(admin_check)
def user_list(request):
    query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')

    users = User.objects.all()

    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    if role_filter:
        users = users.filter(role=role_filter)

    paginator = Paginator(users, 15)  # 15 пользователей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin/user/user_list.html', {
        'page_obj': page_obj,
        'query': query,
        'role_filter': role_filter
    })


@login_required
@user_passes_test(admin_check)
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user)

    return render(request, 'admin/user/user_edit.html', {
        'form': form,
        'user': user,
    })

# ЗАЕЗДЫ --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
@user_passes_test(admin_or_moderator)
def arrival_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')

    arrivals = Arrival.objects.all()

    if query:
        arrivals = arrivals.filter(name__icontains=query)
    if status_filter:
        arrivals = arrivals.filter(status=status_filter)

    paginator = Paginator(arrivals, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'arrivals/arrival_list.html', {
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
    })


@login_required
@user_passes_test(admin_or_moderator)
def arrival_create(request):
    if request.method == 'POST':
        form = ArrivalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('arrival_list')
    else:
        form = ArrivalForm()
    return render(request, 'arrivals/arrival_form.html', {'form': form})


@login_required
@user_passes_test(admin_or_moderator)
def arrival_edit(request, arrival_id):
    arrival = get_object_or_404(Arrival, id=arrival_id)
    if request.method == 'POST':
        form = ArrivalForm(request.POST, instance=arrival)
        if form.is_valid():
            form.save()
            return redirect('arrival_list')
    else:
        form = ArrivalForm(instance=arrival)
    return render(request, 'arrivals/arrival_form.html', {'form': form, 'arrival': arrival})

# ПЛАНИРОВКА --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
@user_passes_test(admin_check)
def room_layout_list(request):
    query = request.GET.get("q", "")
    room_layouts = RoomLayout.objects.all()

    if query:
        room_layouts = room_layouts.filter(
            Q(name__icontains=query) |
            Q(building_type__icontains=query)
        )

    return render(request, "admin/room_layout/room_list.html", {"room_layouts": room_layouts, "query": query})


@login_required
@user_passes_test(admin_check)
def room_layout_create(request):
    if request.method == "POST":
        form = RoomLayoutForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("room_layout_list")
    else:
        form = RoomLayoutForm()
    return render(request, "admin/room_layout/room_form.html", {"form": form, "title": "Создание планировки"})


@login_required
@user_passes_test(admin_check)
def room_layout_edit(request, pk):
    layout = get_object_or_404(RoomLayout, pk=pk)
    if request.method == "POST":
        form = RoomLayoutForm(request.POST, instance=layout)
        if form.is_valid():
            form.save()
            return redirect("room_layout_list")
    else:
        form = RoomLayoutForm(instance=layout)
    return render(request, "admin/room_layout/room_form.html", {"form": form, "title": "Редактирование планировки"})

# РАЗМЕЩЕНИЕ --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
@user_passes_test(admin_or_moderator)
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

    context = {
        "room_placements_map": room_placements_map,
        "rooms_json": mark_safe(json.dumps(rooms_json, cls=DjangoJSONEncoder)),
        "available_guests_json": mark_safe(json.dumps(available_guests_json, cls=DjangoJSONEncoder)),
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
@user_passes_test(admin_or_moderator)
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
        else:
            failed.append(fio_clean)

    if failed:
        return JsonResponse({'success': False, 'not_found': failed})
    return JsonResponse({'success': True})


# ЦЕНЫ --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
@user_passes_test(admin_check)
def rate_list(request):
    query = request.GET.get('q', '')
    building_type_filter = request.GET.get('building_type', '')
    room_layout_filter = request.GET.get('room_layout', '')

    rates = Rate.objects.all()

    if query:
        rates = rates.filter(name__icontains=query)
    if building_type_filter:
        rates = rates.filter(building_type=building_type_filter)
    if room_layout_filter:
        rates = rates.filter(room_layout__id=room_layout_filter)

    room_layouts = RoomLayout.objects.all()
    building_types = Rate.objects.values_list('building_type', flat=True).distinct()

    return render(request, 'admin/rates/rate_list.html', {
        'rates': rates,
        'query': query,
        'building_type_filter': building_type_filter,
        'room_layout_filter': room_layout_filter,
        'room_layouts': room_layouts,
        'building_types': building_types,
    })


@login_required
@user_passes_test(admin_check)
def rate_create(request):
    form = RateForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('rate_list')
    return render(request, 'admin/rates/rate_form.html', {'form': form, "title": "Создание тарифа"})


@login_required
@user_passes_test(admin_check)
def rate_edit(request, pk):
    rate = get_object_or_404(Rate, pk=pk)
    form = RateForm(request.POST or None, instance=rate)
    if form.is_valid():
        form.save()
        return redirect('rate_list')
    return render(request, 'admin/rates/rate_form.html', {'form': form, "title": "Редактирование тарифа"})


# Заявки МОДЕР --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
@user_passes_test(admin_or_moderator)
def moderator_application_list(request):
    arrival_id = request.GET.get('arrival', '')
    status_raw = request.GET.get('status', '')
    status_filter = [s for s in status_raw.split(',') if s]
    query = request.GET.get('q', '')

    # Список заездов для фильтра
    arrivals = Arrival.objects.all().order_by('-start_date')

    applications = Application.objects.none()
    page_obj = None
    positions = {}

    if arrival_id:
        applications = Application.objects.filter(arrival__id=arrival_id).order_by('-created_at')
        if query:
            applications = applications.filter(author__last_name__icontains=query)
        if status_filter:
            applications = applications.filter(status__in=status_filter)

        years = applications.dates('created_at', 'year', order='DESC')
        statuses = Application.STATUS_CHOICES

        paginator = Paginator(applications, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Рассчитываем позиции для sent-заявок в этом заезде
        for app in applications:
            sent_apps = Application.objects.filter(
                arrival=app.arrival,
                status__in=["sent", "revision", "approved"]
            ).order_by('sent_at', 'id')
            for pos, sent_app in enumerate(sent_apps, start=1):
                positions[sent_app.id] = pos
    else:
        years = []
        statuses = Application.STATUS_CHOICES

    return render(request, 'applications/applications_list.html', {
        'arrivals': arrivals,
        'applications': applications,
        'page_obj': page_obj,
        'positions': positions,
        'arrival_id': arrival_id,
        'statuses': statuses,
        'status_filter': status_filter,
        'years': years,
        'query': query,
    })


@login_required
@user_passes_test(admin_or_moderator)
@require_POST
def moderator_application_action(request, app_id):
    action = request.POST.get('action')
    comment = request.POST.get('comment', '')
    app = get_object_or_404(Application, pk=app_id)
    if action == "approve":
        app.status = "approved"
    elif action == "revision":
        app.status = "revision"
        app.comment = comment
    elif action == "reject":
        app.status = "rejected"
    else:
        return JsonResponse({'success': False, 'error': 'Unknown action'})
    app.save()
    return JsonResponse({
        'success': True,
        'status': dict(Application.STATUS_CHOICES).get(app.status, app.status),
        'status_code': app.status
    })

# Заявки  --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
def user_application_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    year_filter = request.GET.get('year', '')

    applications = Application.objects.filter(author=request.user).order_by('-created_at')

    if query:
        applications = applications.filter(arrival__name__icontains=query)
    if status_filter:
        applications = applications.filter(status=status_filter)
    if year_filter:
        applications = applications.filter(created_at__year=year_filter)

    # Список годов для фильтра (например, 2023, 2024)
    years = applications.dates('created_at', 'year', order='DESC')
    statuses = Application.STATUS_CHOICES

    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    now = timezone.now()

    # Для каждой заявки определим ее позицию (по arrival)
    positions = {}
    for app in applications:
        # Берём все отправленные заявки на этот Arrival, сортируем по sent_at
        sent_apps = Application.objects.filter(
            arrival=app.arrival,
            status__in=['sent', 'revision', 'approved']
        ).order_by('sent_at', 'id')  # На всякий случай добавь id для уникальности

        # Составляем mapping: id -> позиция
        for pos, sent_app in enumerate(sent_apps, start=1):
            positions[sent_app.id] = pos

    return render(request, 'user/applications_list.html', {
        'applications': applications,
        'now': now,
        'positions': positions,  # Добавляем в шаблон
        'page_obj': page_obj,
        'query': query,
        'status_filter': status_filter,
        'year_filter': year_filter,
        'years': years,
        'statuses': statuses,
    })


@login_required
def user_application_create(request):
    user = request.user
    free_quota = user.get_free_quota()
    rates = list(Rate.objects.values('id', 'name'))
    relatives = Relative.objects.filter(user=user)
    relatives_list = [
        {
            "id": r.id,
            "last_name": r.last_name,
            "first_name": r.first_name,
            "patronymic": r.patronymic,
            "birthdate": r.birthdate.strftime("%Y-%m-%d") if r.birthdate else "",
            "relation": r.relation,
        } for r in relatives
    ]
    user_data = {
        "id": user.id,
        "last_name": user.last_name or "",
        "first_name": user.first_name or "",
        "patronymic": user.patronymic or "",
        "birthdate": user.birthdate.strftime("%Y-%m-%d") if user.birthdate else "",
        "relation": "Сотрудник",
    }

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        form.free_quota = user.get_free_quota()

        try:
            guests = json.loads(request.POST.get('guests', '[]'))
            preferential_quote = [g for g in guests if g.get('quota_type') == 'Льготная квота']
            preferential_need = len(preferential_quote)
            if preferential_need > user.get_free_quota(exclude_application=None):
                messages.error(request,f"Вы указали {preferential_need} льготных квот, а доступно только {user.get_free_quota(exclude_application=None)}.")
                return render(request, 'user/application_form.html', {
                    'form': form,
                    'guests_json': '[]',
                    'free_quota': free_quota,
                    'user_data': json.dumps(user_data, cls=DjangoJSONEncoder),
                    'relatives_data': json.dumps(relatives_list, cls=DjangoJSONEncoder),
                    'relatives': relatives,
                    'rates': rates,
                })
        except Exception as ex:
            messages.error(request, "Ошибка проверки квот. Проверьте заполнение отдыхающих.")
            return render(request, ...)

        if form.is_valid():
            application = form.save(commit=False)
            application.author = user
            application.save()
            messages.success(request, "Заявка успешно отправлена!")
            return redirect('user_dashboard')
        else:
            print("Форма невалидна", form.errors)
    else:
        form = ApplicationForm()

    return render(request, 'user/application_form.html', {
        'form': form,
        'guests_json': '[]',
        'free_quota': free_quota,
        'user_data': json.dumps(user_data, cls=DjangoJSONEncoder),
        'relatives_data': json.dumps(relatives_list, cls=DjangoJSONEncoder),
        'relatives': relatives,
        'rates': rates,
    })


# Действия с заявками  --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
def send_application(request, app_id):
    application = get_object_or_404(Application, id=app_id, author=request.user)
    now = timezone.now()
    # Проверка, что окно подачи открыто
    if not (application.arrival.application_start <= now <= application.arrival.application_end):
        messages.error(request, "Время подачи заявок истекло или не наступило!")
        return redirect('user_applications_list')

    if request.method == "POST":
        application.status = 'sent'
        application.sent_at = now
        application.save()
        messages.success(request, "Заявка успешно отправлена!")
        return redirect('user_applications_list')

    return redirect('user_applications_list')


@login_required
@require_POST
def delete_application(request, app_id):
    app = get_object_or_404(Application, id=app_id, author=request.user)
    if app.status == 'new':
        app.delete()
        messages.success(request, "Заявка удалена.")
    else:
        messages.error(request, "Удалять можно только новые заявки.")
    return redirect('user_applications_list')


@login_required
@require_POST
def revoke_application(request, app_id):
    app = get_object_or_404(Application, id=app_id, author=request.user)
    if app.status == 'sent':
        app.status = 'cancelled'
        app.save()
        messages.success(request, "Заявка отозвана.")
    else:
        messages.error(request, "Отзывать можно только отправленные заявки.")
    return redirect('user_applications_list')


@login_required
def user_application_edit(request, app_id):
    app = get_object_or_404(Application, id=app_id, author=request.user)
    if app.status not in ['new', 'revision']:
        messages.error(request, "Редактирование невозможно для этой заявки.")
        return redirect('user_applications_list')

    user = request.user
    guests_json = app.guests if app.guests else '[]'
    initial_guests = json.loads(guests_json)
    # preferential_count = len([g for g in initial_guests if g.get('quota_type') == 'Льготная квота'])
    free_quota = user.get_free_quota(exclude_application=app)# - preferential_count

    rates = list(Rate.objects.values('id', 'name'))

    relatives = Relative.objects.filter(user=user)
    relatives_list = [
        {
            "id": r.id,
            "last_name": r.last_name,
            "first_name": r.first_name,
            "patronymic": r.patronymic,
            "birthdate": r.birthdate.strftime("%Y-%m-%d") if r.birthdate else "",
            "relationship": r.relation,
        } for r in relatives
    ]
    user_data = {
        "id": user.id,
        "last_name": user.last_name or "",
        "first_name": user.first_name or "",
        "patronymic": user.patronymic or "",
        "birthdate": user.birthdate.strftime("%Y-%m-%d") if user.birthdate else "",
        "relationship": "Сотрудник",
    }

    if request.method == 'POST':
        form = ApplicationEditForm(request.POST, request.FILES, instance=app)
        form.free_quota = user.get_free_quota(exclude_application=app)

        try:
            guests = json.loads(request.POST.get('guests', '[]'))
            preferential_quote = [g for g in guests if g.get('quota_type') == 'Льготная квота']
            preferential_need = len(preferential_quote)
            if preferential_need > user.get_free_quota(exclude_application=app):
                messages.error(request,f"Вы указали {preferential_need} льготных квот, а доступно только {user.get_free_quota(exclude_application=app)}.")
                return render(request, 'user/application_edit.html', {
                    'form': form,
                    'app': app,
                    'free_quota': free_quota,
                    'guests_json': guests_json,
                    'user_data': json.dumps(user_data, cls=DjangoJSONEncoder),
                    'relatives_data': json.dumps(relatives_list, cls=DjangoJSONEncoder),
                    'initialGuests': initial_guests,
                    'rates': rates,
                })
        except Exception as ex:
            messages.error(request, "Ошибка проверки квот. Проверьте заполнение отдыхающих.")
            return render(request, ...)

        if form.is_valid():
            application = form.save(commit=False)
            if application.status == 'revision':
                application.status = 'sent'
                if not application.sent_at:
                    from django.utils import timezone
                    application.sent_at = timezone.now()
            application.save()
            messages.success(request, "Заявка успешно отправлена!")
            return redirect('user_applications_list')
    else:
        form = ApplicationEditForm(instance=app)

    return render(request, 'user/application_edit.html', {
        'form': form,
        'app': app,
        'free_quota': free_quota,
        'guests_json': guests_json,
        'user_data': json.dumps(user_data, cls=DjangoJSONEncoder),
        'relatives_data': json.dumps(relatives_list, cls=DjangoJSONEncoder),
        'initialGuests': json.dumps(initial_guests, cls=DjangoJSONEncoder),
        'rates': rates,
    })


# Родственники  --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
@user_passes_test(admin_check)
def relatives_list(request):
    relatives = Relative.objects.select_related('user').all()
    return render(request, 'admin/relatives/relatives_list.html', {'relatives': relatives})


@login_required
@user_passes_test(admin_check)
def relative_create(request):
    # тут должна быть ваша форма RelativeForm
    from .forms import RelativeForm
    if request.method == "POST":
        form = RelativeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('relatives_list')
    else:
        form = RelativeForm()
    return render(request, 'admin/relatives/relative_form.html', {'form': form, 'title': 'Добавить родственника'})


@login_required
@user_passes_test(admin_check)
def relative_edit(request, relative_id):
    from .forms import RelativeForm
    relative = get_object_or_404(Relative, id=relative_id)
    if request.method == "POST":
        form = RelativeForm(request.POST, instance=relative)
        if form.is_valid():
            form.save()
            return redirect('relatives_list')
    else:
        form = RelativeForm(instance=relative)
    return render(request, 'admin/relatives/relative_form.html', {'form': form, 'title': 'Редактировать родственника'})



# Дашбоарды  --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
@user_passes_test(admin_check)
def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html')


@login_required
def moderator_dashboard(request):
    return render(request, 'dashboards/moderator_dashboard.html')


@login_required
def user_dashboard(request):
    return render(request, 'dashboards/user_dashboard.html')


@login_required
def dashboard_redirect(request):
    role = getattr(request.user, 'role', None)
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'moderator':
        return redirect('moderator_dashboard')
    else:
        return redirect('user_dashboard')
