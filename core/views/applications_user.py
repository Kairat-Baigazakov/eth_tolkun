# application_user.py
import json
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.core.paginator import Paginator
from ..models import Rate, Application, Relative, ApplicationDocument
from ..forms import ApplicationForm, ApplicationEditForm, ApplicationDocumentForm
from django.core.serializers.json import DjangoJSONEncoder


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

    # --- Готовим тарифы для JS ---
    rates = Rate.objects.all()
    rates_map = {}

    # ВАЖНО: ключи делаем строками: "<building_type>::<quota>"
    def put(bt, qt, price, nds, nsp, nma):
        key = f"{bt}::{qt}"
        rates_map[key] = {
            "price": str(price),  # str, чтобы JSON гарантированно был сериализуемым
            "nds": str(nds),
            "nsp": str(nsp),
            "nma": str(nma),
        }


    for rate in rates:
        # Полная
        put(rate.building_type, "Полная стоимость",
            rate.price_full, rate.nds_full, rate.nsp_full, rate.nma_full)

        # 50% стоимость
        put(rate.building_type, "50% стоимость",
            rate.price_50, rate.nds_50, rate.nsp_50, rate.nma_50)

        # Льготная — активный вариант
        if rate.lgot_active_set == 1:
            put(rate.building_type, "Льготная квота",
                rate.price_lgot_1, rate.nds_lgot_1, rate.nsp_lgot_1, rate.nma_lgot_1)
        else:
            put(rate.building_type, "Льготная квота",
                rate.price_lgot_2, rate.nds_lgot_2, rate.nsp_lgot_2, rate.nma_lgot_2)


    # --- Для каждой заявки собираем гостей и используемый building_type ---
    apps_guests = []
    for app in applications:
        try:
            guests = json.loads(app.guests or '[]')
        except Exception:
            guests = []
        # Простой способ: если у всей заявки один building_type (корпус) — вытащи его из app.rooms
        # Если rooms вида "101, 2 этаж, Корпус №3" => ищи "Корпус №N" регуляркой

        building_type = ""
        if app.rooms:
            m = re.search(r'Корпус №(\d+)', app.rooms)
            if m:
                building_type = m.group(1)
            m = re.search(r'Корпус люкс №(\d+)', app.rooms)
            if m:
                building_type = "lux" + m.group(1)
        apps_guests.append({
            "id": app.id,
            "guests": guests,
            "building_type": building_type,
        })

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
        # Для JS:
        'rates_map_json': mark_safe(json.dumps(rates_map)),
        'applications_guests_json': mark_safe(json.dumps(apps_guests)),
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
        form = ApplicationForm(request.POST)
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
            messages.success(request, "Заявка успешно создана! Теперь вы можете прикрепить документы.")
            return redirect('user_application_edit', app_id=application.id)
        else:
            print("Форма невалидна", form.errors)
            return render(request, 'user/application_form.html', {
                'form': form,
                'guests_json': '[]',
                'free_quota': free_quota,
                'user_data': json.dumps(user_data, cls=DjangoJSONEncoder),
                'relatives_data': json.dumps(relatives_list, cls=DjangoJSONEncoder),
                'relatives': relatives,
                'rates': rates,
            })
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
            for file in request.FILES.getlist('files'):
                ApplicationDocument.objects.create(application=application, file=file)
            messages.success(request, "Заявка успешно отправлена!")
            return redirect('user_applications_list')
        else:
            print("Форма невалидна", form.errors)
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
