from django.shortcuts import render, redirect, get_object_or_404
from core.decorators import admin_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import User
from ..forms import UserCreationForm, UserEditForm

User = get_user_model()

@login_required
@admin_required
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
@admin_required
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
@admin_required
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