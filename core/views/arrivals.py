from django.shortcuts import render, redirect, get_object_or_404
from core.decorators import admin_or_moderator_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from ..models import Arrival
from ..forms import ArrivalForm


@login_required
@admin_or_moderator_required
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
@admin_or_moderator_required
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
@admin_or_moderator_required
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