from django.shortcuts import render, redirect, get_object_or_404
from .models import Arrival, Application, Relative
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .forms import ApplicationForm
from django.utils import timezone
from django.shortcuts import render


def user_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'user':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def arrival_list(request):
    now = timezone.now()
    arrivals = Arrival.objects.filter(apply_start__lte=now, apply_end__gte=now)
    return render(request, 'core/arrival_list.html', {'arrivals': arrivals})


@user_only
@login_required
def apply_for_arrival(request, arrival_id):
    arrival = get_object_or_404(Arrival, pk=arrival_id)
    if request.method == 'POST':
        form = ApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.arrival = arrival
            application.save()
            form.cleaned_data['relatives'].update(application=application)
            return redirect('arrival_list')
    else:
        form = ApplicationForm(user=request.user)
    return render(request, 'core/application_form.html', {'form': form, 'arrival': arrival})


def moderator_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'moderator':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@moderator_only
def moderator_applications_list(request):
    applications = Application.objects.select_related('user', 'arrival').order_by('-created_at')
    return render(request, 'core/moderator_applications_list.html', {'applications': applications})


@login_required
@moderator_only
def moderator_approve(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    app.status = 'approved'
    app.save()
    return redirect('moderator_applications_list')


@login_required
@moderator_only
def moderator_reject(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    app.status = 'rejected'
    app.save()
    return redirect('moderator_applications_list')
