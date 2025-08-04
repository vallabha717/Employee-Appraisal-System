from django.urls import path
from . import views
from accounts import views as account_views

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/submit/', views.submit_task, name='submit_task'),
    path('rate/<int:employee_id>/', views.rate_employee, name='rate_employee'),
    path('appraisal/create/<int:employee_id>/', views.create_appraisal, name='create_appraisal'),
    path('appraisal/<int:appraisal_id>/', views.view_appraisal, name='view_appraisal'),
    path('appraisal/<int:appraisal_id>/negotiate/', views.negotiate_appraisal, name='negotiate_appraisal'),
    path('appraisal/<int:appraisal_id>/pdf/', views.generate_appraisal_pdf, name='generate_appraisal_pdf'),
    path('appraisal/<int:appraisal_id>/approve/', views.approve_appraisal, name='approve_appraisal'),
    path('appraisal/<int:appraisal_id>/accept/', account_views.accept_appraisal, name='accept_appraisal'),
    path('appraisal/<int:appraisal_id>/edit-scores/', views.edit_appraisal_scores, name='edit_appraisal_scores'),
    path('period/create/', views.create_appraisal_period, name='create_appraisal_period'),
    path('period/<int:period_id>/edit/', views.edit_appraisal_period, name='edit_appraisal_period'),
]