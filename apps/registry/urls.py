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

    # Staff Detail
    path('staff/<int:staff_id>/', views.staff_detail, name='staff_detail'),
]
