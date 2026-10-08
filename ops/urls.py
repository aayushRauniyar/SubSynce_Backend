from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy
from . import views, views_calendar, views_invoices, views_reports, views_settings, views_work
from .forms import OpsPasswordResetForm

# App namespace - allows us to use 'ops:login', 'ops:dashboard', etc.
app_name = 'ops'

urlpatterns = [
    # Login page (root URL)
    path('', views.login_view, name='login'),
    
    # Dashboard (protected - requires login)
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Clients (protected - Administrator only)
    path('clients/', views.clients_view, name='clients'),
    path('clients/add/', views.client_create_view, name='client_create'),
    path('clients/<uuid:pk>/', views.client_detail_view, name='client_detail'),
    path('clients/<uuid:pk>/edit/', views.client_update_view, name='client_update'),
    path('clients/<uuid:pk>/delete/', views.client_delete_view, name='client_delete'),

    # Sites (protected - Administrator only)
    path('sites/', views.sites_view, name='sites'),
    path('sites/add/', views.site_create_view, name='site_create'),
    path('sites/<uuid:pk>/edit/', views.site_update_view, name='site_update'),
    path('sites/<uuid:pk>/delete/', views.site_delete_view, name='site_delete'),

    # Schedules (protected - Administrator only)
    path('schedules/', views.schedules_view, name='schedules'),
    path('schedules/add/', views.schedule_create_view, name='schedule_create'),
    path('schedules/<uuid:pk>/edit/', views.schedule_update_view, name='schedule_update'),
    path('schedules/<uuid:pk>/status/', views.schedule_status_view, name='schedule_status'),
    path('schedules/<uuid:pk>/delete/', views.schedule_delete_view, name='schedule_delete'),

    # User management (Administrators and Owners)
    path('users/', views.users_view, name='users'),
    path('users/add/', views.user_create_view, name='user_create'),
    path('users/<uuid:pk>/edit/', views.user_update_view, name='user_update'),
    path('users/<uuid:pk>/delete/', views.user_delete_view, name='user_delete'),

    # Subcontractors (protected - Administrator only, read-only)
    path('subcontractors/', views.subcontractors_view, name='subcontractors'),

    # Password reset (Django's built-in views and tokens)
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='ops/password_reset.html',
        form_class=OpsPasswordResetForm,
        email_template_name='ops/emails/password_reset_email.txt',
        subject_template_name='ops/emails/password_reset_subject.txt',
        success_url=reverse_lazy('ops:password_reset_done'),
    ), name='password_reset'),
    path('forgot-password/sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='ops/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='ops/password_reset_confirm.html',
        success_url=reverse_lazy('ops:password_reset_complete'),
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='ops/password_reset_complete.html',
    ), name='password_reset_complete'),

    # Contractor portal quick actions (session versions of the work API's clock-in/out)
    path('portal/check-in/', views.portal_check_in_view, name='portal_check_in'),
    path('portal/check-out/', views.portal_check_out_view, name='portal_check_out'),

    # Work completion (contractor clock-in/out, staff log)
    path('jobs/', views_work.my_jobs_view, name='my_jobs'),
    path('jobs/<uuid:schedule_id>/clock-in/', views_work.clock_in_view, name='clock_in'),
    path('work/<uuid:work_id>/clock-out/', views_work.clock_out_view, name='clock_out'),
    path('work/<uuid:work_id>/', views_work.work_detail_view, name='work_detail'),
    path('completions/', views_work.completions_view, name='completions'),
    path('completions/<uuid:work_id>/', views_work.work_detail_view, name='completion_detail'),

    # Contractor invoices (builder, verification, print)
    path('invoices/', views_invoices.invoice_list_view, name='invoices'),
    path('invoices/new/', views_invoices.invoice_create_view, name='invoice_create'),
    path('invoices/<uuid:pk>/', views_invoices.invoice_detail_view, name='invoice_detail'),
    path('invoices/<uuid:pk>/edit/', views_invoices.invoice_edit_view, name='invoice_edit'),
    path('invoices/<uuid:pk>/delete/', views_invoices.invoice_delete_view, name='invoice_delete'),
    path('invoices/<uuid:pk>/decide/', views_invoices.invoice_decide_view, name='invoice_decide'),
    path('invoices/<uuid:pk>/print/', views_invoices.invoice_print_view, name='invoice_print'),

    # Calendar
    path('calendar/', views_calendar.calendar_view, name='calendar'),
    path('calendar/mine/', views_calendar.my_calendar_view, name='my_calendar'),

    # Reports
    path('reports/profitability/', views_reports.profitability_view, name='profitability'),

    # Settings (Owner only)
    path('settings/company/', views_settings.company_settings_view, name='company_settings'),

    # Logout
    path('logout/', views.logout_view, name='logout'),
]
