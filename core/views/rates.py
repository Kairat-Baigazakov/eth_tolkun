from django.shortcuts import render, redirect, get_object_or_404
from core.decorators import admin_required
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from ..models import Rate, RoomLayout
from ..forms import RateForm


@login_required
@admin_required
def rate_list(request):
    query = request.GET.get('q', '')
    building_type_filter = request.GET.get('building_type')

    rates = Rate.objects.all()

    if query:
        rates = rates.filter(name__icontains=query)
    if building_type_filter:
        rates = rates.filter(building_type=building_type_filter)

    building_types = RoomLayout.BUILDING_TYPE_CHOICES

    return render(request, 'admin/rates/rate_list.html', {
        'rates': rates,
        'query': query,
        'building_type_filter': building_type_filter,
        'building_types': building_types,
    })


@login_required
@admin_required
def rate_create(request):
    form = RateForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('rate_list')
    return render(request, 'admin/rates/rate_form.html', {'form': form, "title": "Создание тарифа"})


@login_required
@admin_required
def rate_edit(request, pk):
    rate = get_object_or_404(Rate, pk=pk)
    form = RateForm(request.POST or None, instance=rate)
    if form.is_valid():
        form.save()
        return redirect('rate_list')
    return render(request, 'admin/rates/rate_form.html', {'form': form, "title": "Редактирование тарифа"})


@require_POST
def set_active_rate(request):
    rate_id = request.POST.get('rate_id')
    lgot_active_set  = request.POST.get('lgot_active_set')

    try:
        rate = Rate.objects.get(id=rate_id)
        rate.lgot_active_set = int(lgot_active_set)
        rate.save(update_fields=['lgot_active_set'])
        return JsonResponse({'success': True})
    except Rate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Rate not found'})
    except Exception as ex:
        return JsonResponse({'success': False, 'error': str(ex)})