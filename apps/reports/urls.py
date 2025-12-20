from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Dashboard สรุป (Officer/Admin)
    path('dashboard/', views.dashboard_summary, name='dashboard_summary'),

    # รายงานตามประเภทบัตร
    path('badge-type/', views.report_by_badge_type, name='report_by_badge_type'),

    # รายงานตามหน่วยงาน
    path('department/', views.report_by_department, name='report_by_department'),
    path('department/<int:department_id>/badge-receipt/', views.badge_receipt_report_pdf, name='badge_receipt_pdf'),
    path('department/<int:department_id>/printing-status/', views.badge_printing_status_pdf, name='badge_printing_status_pdf'),
    path('department/<int:department_id>/detailed-report/', views.department_detailed_report_pdf, name='department_detailed_report_pdf'),
    path('department/<int:department_id>/badge-type/<int:badge_type_id>/report/', views.department_badge_type_report_pdf, name='department_badge_type_report_pdf'),
    path('department/<int:department_id>/export-excel/', views.department_staff_export_excel, name='department_staff_export_excel'),

    # รายงานหน่วยงาน (Submitter)
    path('my-department/', views.submitter_report, name='submitter_report'),

    # ตรวจสอบข้อมูลซ้ำ (Officer/Admin)
    path('duplicates/', views.duplicate_check_view, name='duplicate_check'),

    # Print Manager - จัดการการพิมพ์บัตร
    path('print-manager/', views.print_manager_dashboard, name='print_manager'),
]
