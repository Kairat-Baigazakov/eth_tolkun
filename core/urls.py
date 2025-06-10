from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import logout_view, admin_dashboard, moderator_dashboard, user_dashboard, CustomLoginView, dashboard_redirect, user_create, user_list, user_edit

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/moderator/', moderator_dashboard, name='moderator_dashboard'),
    path('dashboard/user/', user_dashboard, name='user_dashboard'),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/admin/create_user/', user_create, name='user_create'),
    path('dashboard/admin/users/', user_list, name='user_list'),
    path('users/<int:user_id>/edit/', user_edit, name='user_edit'),

    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='account/change_password.html',
        success_url=reverse_lazy('password_change_done')
    ), name='change_password'),

    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='account/password_change_done.html'
    ), name='password_change_done'),
]
