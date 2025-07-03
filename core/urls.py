from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    logout_view,
    admin_dashboard,
    moderator_dashboard,
    user_dashboard,
    CustomLoginView,
    dashboard_redirect,
    user_create,
    user_list,
    user_edit,
    arrival_list,
    arrival_create,
    arrival_edit,
    rate_list,
    rate_create,
    rate_edit,
    room_layout_list,
    room_layout_create,
    room_layout_edit,
    user_application_list,
    user_application_create,
    user_application_edit,
    send_application,
    delete_application,
    revoke_application,
    relatives_list,
    relative_create,
    relative_edit,
    moderator_application_list,
    moderator_application_action,
    placement_page,
    save_placements
)

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

    path('dashboard/admin/relatives/', relatives_list, name='relatives_list'),
    path('dashboard/admin/relatives/create/', relative_create, name='relative_create'),
    path('dashboard/admin/relatives/<int:relative_id>/edit/', relative_edit, name='relative_edit'),

    path('dashboard/admin/rates/', rate_list, name='rate_list'),
    path('dashboard/admin/rates/create/', rate_create, name='rate_create'),
    path('dashboard/admin/rates/<int:rate_id>/edit/', rate_edit, name='rate_edit'),

    path('dashboard/admin/room-layout/', room_layout_list, name='room_layout_list'),
    path('dashboard/admin/room-layout/create/', room_layout_create, name='room_layout_create'),
    path('dashboard/admin/room-layout/<int:pk>/edit/', room_layout_edit, name='room_layout_edit'),

    path('dashboard/arrivals/', arrival_list, name='arrival_list'),
    path('dashboard/arrivals/create/', arrival_create, name='arrival_create'),
    path('dashboard/arrivals/<int:arrival_id>/edit/', arrival_edit, name='arrival_edit'),

    path('dashboard/user/applications/', user_application_list, name='user_applications_list'),
    path('dashboard/user/applications/create/', user_application_create, name='user_application_create'),
    path('applications/send/<int:app_id>/', send_application, name='send_application'),
    path('applications/delete/<int:app_id>/', delete_application, name='delete_application'),
    path('applications/revoke/<int:app_id>/', revoke_application, name='revoke_application'),
    path('applications/<int:app_id>/edit/', user_application_edit, name='user_application_edit'),

    path('applications/', moderator_application_list, name='moderator_application_list'),
    path('applications/<int:app_id>/action/', moderator_application_action, name='moderator_application_action'),

    path('placement/', placement_page, name='placement_page'),
    path('placements/save/', save_placements, name='save_placements'),

    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='account/change_password.html',
        success_url=reverse_lazy('password_change_done')
    ), name='change_password'),

    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='account/password_change_done.html'
    ), name='password_change_done'),
]
