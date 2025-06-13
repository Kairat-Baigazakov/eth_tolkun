import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import logout, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Arrival, Rate, RoomLayout, Application, Relative
from .forms import LoginForm, UserCreationForm, UserEditForm, ArrivalForm, RateForm, RoomLayoutForm, ApplicationForm, RelativeForm
from django.core.serializers.json import DjangoJSONEncoder

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


# Заявки  --------------------------------------------------------------------------------------------------------------------------------------------------
@login_required
def user_application_list(request):
    applications = Application.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'user/applications_list.html', {
        'applications': applications,
    })


@login_required
def user_application_create(request):
    user = request.user
    user_quota = user.total_quota
    relatives = Relative.objects.filter(user=user)  # <-- ForeignKey!

    # Для JS — relatives как список словарей
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
    # Для JS — user
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
        'user_quota': user_quota,
        'user_data': json.dumps(user_data, cls=DjangoJSONEncoder),
        'relatives_data': json.dumps(relatives_list, cls=DjangoJSONEncoder),
        'relatives': relatives,
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
