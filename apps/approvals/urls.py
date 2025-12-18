from django.urls import path
from . import views

app_name = 'approvals'

urlpatterns = [
    # Pending requests
    path('pending/', views.pending_list, name='pending_list'),
    path('review/<int:request_id>/', views.review_detail, name='review_detail'),

    # Actions
    path('approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('send-back/<int:request_id>/', views.send_back_for_revision, name='send_back_for_revision'),

    # Bulk actions
    path('bulk/approve/', views.bulk_approve, name='bulk_approve'),
    path('bulk/reject/', views.bulk_reject, name='bulk_reject'),
    path('bulk/edit-approved/', views.bulk_edit_approved, name='bulk_edit_approved'),  # Bulk edit for approved items
    path('bulk/send-back-for-revision/', views.bulk_send_back_for_revision, name='bulk_send_back_for_revision'),  # Bulk send back from approved

    # Lists
    path('approved/', views.approved_list, name='approved_list'),
    path('rejected/', views.rejected_list, name='rejected_list'),

    # Edit
    path('edit/<int:request_id>/', views.edit_approved, name='edit_approved'),

    # History
    path('history/', views.approval_history, name='history'),
]
