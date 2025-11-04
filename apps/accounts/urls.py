from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # User Management
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),

    # Department Management
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/<int:dept_id>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:dept_id>/delete/', views.department_delete, name='department_delete'),
]
