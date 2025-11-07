"""
URL configuration for badges app
"""
from django.urls import path
from . import views
from . import views_signatory

app_name = 'badges'

urlpatterns = [
    # Badge management
    path('list/', views.badge_list, name='badge_list'),
    path('<int:badge_id>/', views.badge_detail, name='badge_detail'),
    path('create/<int:request_id>/', views.create_badge, name='create_badge'),
    path('<int:badge_id>/update-signature/', views.update_signature, name='update_signature'),
    path('<int:badge_id>/print/', views.print_badge, name='print_badge'),
    path('<int:badge_id>/delete/', views.delete_badge, name='delete_badge'),

    # Signatory management
    path('signatories/', views_signatory.signatory_list, name='signatory_list'),
    path('signatories/create/', views_signatory.signatory_create, name='signatory_create'),
    path('signatories/<int:signatory_id>/edit/', views_signatory.signatory_edit, name='signatory_edit'),
    path('signatories/<int:signatory_id>/delete/', views_signatory.signatory_delete, name='signatory_delete'),
]
