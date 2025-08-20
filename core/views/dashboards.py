from django.shortcuts import render, redirect
from core.decorators import admin_required, moderator_required, user_required
from django.contrib.auth.decorators import login_required

@login_required
@admin_required
def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html')


@login_required
@moderator_required
def moderator_dashboard(request):
    return render(request, 'dashboards/moderator_dashboard.html')


@login_required
@user_required
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
