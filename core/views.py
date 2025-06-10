from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import LoginForm, UserCreationForm, UserEditForm


User = get_user_model()


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


def admin_check(user):
    return user.is_authenticated and user.role == 'admin'


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
    return render(request, 'admin/user_create.html', {'form': form})


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

    return render(request, 'admin/user_list.html', {
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

    return render(request, 'admin/user_edit.html', {
        'form': form,
        'user': user,
    })


def logout_view(request):
    logout(request)
    return redirect('login')


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
