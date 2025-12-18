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
    path('create/<int:request_id>/', views.create_badge, name='create_badge'),
    path('bulk-create/', views.bulk_create_badge, name='bulk_create_badge'),
    path('bulk-delete/', views.bulk_delete_badge, name='bulk_delete_badge'),
    path('bulk-reset-print/', views.bulk_reset_print, name='bulk_reset_print'),
    path('<int:badge_id>/edit/', views.edit_badge, name='edit_badge'),
    path('<int:badge_id>/update-photo/', views.update_badge_photo, name='update_badge_photo'),
    path('<int:badge_id>/update-signature/', views.update_signature, name='update_signature'),
    path('<int:badge_id>/print/', views.print_badge, name='print_badge'),
    path('<int:badge_id>/delete/', views.delete_badge, name='delete_badge'),
    path('<int:badge_id>/', views.badge_detail, name='badge_detail'),  # Keep this last as catch-all

    # Print Manager (A4 Layout)
    path('print/', views.print_manager, name='print_manager'),
    path('print/preview/', views.print_preview, name='print_preview'),
    path('print/generate-pdf/', views.generate_print_pdf, name='generate_print_pdf'),

    # Print Range (Range Selection)
    path('print-range/', views.print_range, name='print_range'),
    path('print-range/preview/', views.preview_range, name='preview_range'),
    path('print-range/generate-pdf/', views.generate_range_pdf, name='generate_range_pdf'),

    # Signatory management
    path('signatories/', views_signatory.signatory_list, name='signatory_list'),
    path('signatories/create/', views_signatory.signatory_create, name='signatory_create'),
    path('signatories/<int:signatory_id>/edit/', views_signatory.signatory_edit, name='signatory_edit'),
    path('signatories/<int:signatory_id>/delete/', views_signatory.signatory_delete, name='signatory_delete'),
]
