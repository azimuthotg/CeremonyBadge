from django.urls import path
from . import views

app_name = 'registry'

urlpatterns = [
    # Staff List
    path('staff/', views.staff_list, name='staff_list'),

    # Wizard
    path('wizard/step1/', views.wizard_step1, name='wizard_step1'),
    path('wizard/step1/<int:staff_id>/', views.wizard_step1, name='wizard_step1_edit'),
    path('wizard/step2/<int:staff_id>/', views.wizard_step2, name='wizard_step2'),
    path('wizard/step3/<int:staff_id>/', views.wizard_step3, name='wizard_step3'),
    path('wizard/submit/<int:request_id>/', views.wizard_submit, name='wizard_submit'),

    # Staff Detail & Delete
    path('staff/<int:staff_id>/', views.staff_detail, name='staff_detail'),
    path('staff/<int:staff_id>/delete/', views.staff_delete, name='staff_delete'),

    # Badge Type Management
    path('settings/badge-types/', views.badge_type_list, name='badge_type_list'),
    path('settings/badge-types/<int:badge_type_id>/edit/', views.badge_type_edit, name='badge_type_edit'),
    path('settings/badge-types/<int:badge_type_id>/delete/', views.badge_type_delete, name='badge_type_delete'),

    # Zone Management
    path('settings/zones/', views.zone_list, name='zone_list'),
    path('settings/zones/create/', views.zone_create, name='zone_create'),
    path('settings/zones/<int:zone_id>/edit/', views.zone_edit, name='zone_edit'),
    path('settings/zones/<int:zone_id>/delete/', views.zone_delete, name='zone_delete'),
]
