from django.urls import path
from . import views

urlpatterns = [
    path('', views.arrival_list, name='arrival_list'),
    path('apply/<int:arrival_id>/', views.apply_for_arrival, name='apply_for_arrival'),
    path('moderator/applications/', views.moderator_applications_list, name='moderator_applications_list'),
    path('moderator/applications/<int:app_id>/approve/', views.moderator_approve, name='moderator_approve'),
    path('moderator/applications/<int:app_id>/reject/', views.moderator_reject, name='moderator_reject'),
    path('moderator/dashboard/', views.moderator_dashboard, name='moderator_dashboard'),
    path('superadmin/dashboard/', views.superadmin_dashboard, name='superadmin_dashboard'),
]
