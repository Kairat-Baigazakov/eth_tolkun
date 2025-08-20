# documents.py
from django.shortcuts import get_object_or_404
from core.decorators import admin_or_moderator_required
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from ..models import Application, ApplicationDocument
from django.http import JsonResponse

@login_required
def upload_documents(request, app_id):
    app = get_object_or_404(Application, id=app_id, author=request.user)
    files = request.FILES.getlist('files')
    if files:
        for f in files:
            ApplicationDocument.objects.create(application=app, file=f)
        # Статус можно менять тут по ситуации, если это именно платеж:
        if 'payment' in request.POST.get('doc_type', ''):
            app.payment_status = 'check_pay'
            app.save(update_fields=['payment_status'])
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Нет файлов'})


@login_required
@admin_or_moderator_required
@require_POST
def approve_payment(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    app.payment_status = 'paid'
    app.save(update_fields=['payment_status'])
    return JsonResponse({'success': True})


@login_required
@require_POST
def payment_check(request, app_id):
    app = get_object_or_404(Application, id=app_id, author=request.user)
    files = request.FILES.getlist('files')
    # Если только один файл, сохраняем в поле document
    if files:
        for f in files:
            ApplicationDocument.objects.create(application=app, file=f)
        app.payment_status = 'check_pay'
        app.save(update_fields=['payment_status'])
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Файл не выбран'})