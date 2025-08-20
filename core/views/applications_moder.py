# application_moder.py
from django.shortcuts import render, get_object_or_404
from core.decorators import admin_or_moderator_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ..models import Arrival, Application
import json


@login_required
@admin_or_moderator_required
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
        'role': getattr(request.user, 'role', None),
    })


@login_required
@admin_or_moderator_required
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
    elif action == "mark_payment_pending":
        # 1. Проверка, что все гости размещены
        guests = json.loads(app.guests or '[]')
        # Получаем ФИО всех гостей из заявки
        guests_fio = [
            " ".join([
                g.get('last_name', '').strip(),
                g.get('first_name', '').strip(),
                g.get('patronymic', '').strip()
            ]).strip()
            for g in guests
            if g.get('last_name') or g.get('first_name')
        ]
        # Получаем ФИО всех размещённых гостей
        placements = list(app.placements.values_list('guest_fio', flat=True))
        # Сравниваем списки: все ли гости из заявки размещены
        all_placed = all(fio in placements for fio in guests_fio)
        if not all_placed:
            return JsonResponse(
                {'success': False, 'error': 'Не все гости размещены по комнатам. Сначала разместите всех гостей.'})

        # Только если все гости размещены, можно продолжить оплату
        if app.status == "approved" and (app.payment_status == "unpaid" or app.payment_status == "check_pay"):
            app.payment_status = "pending"
            app.save(update_fields=["payment_status"])
            return JsonResponse({'success': True, 'payment_status': 'pending'})
        else:
            return JsonResponse(
                {'success': False, 'error': 'Можно изменить статус оплаты только для одобренных и неоплаченных заявок'}
            )
    else:
        return JsonResponse({'success': False, 'error': 'Unknown action'})
    app.save()
    return JsonResponse({
        'success': True,
        'status': dict(Application.STATUS_CHOICES).get(app.status, app.status),
        'status_code': app.status
    })
