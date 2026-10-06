from django.urls import path
from . import views, views_calendar, views_client_invoices, views_invoices, views_reports, views_settings, views_work

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
    path('clients/<uuid:pk>/edit/', views.client_update_view, name='client_update'),
    path('clients/<uuid:pk>/delete/', views.client_delete_view, name='client_delete'),

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

    # Client invoices (what the company bills clients; Admin and Owner)
    path('client-invoices/', views_client_invoices.client_invoice_list_view, name='client_invoices'),
    path('client-invoices/new/', views_client_invoices.client_invoice_create_view, name='client_invoice_create'),
    path('client-invoices/<uuid:pk>/', views_client_invoices.client_invoice_detail_view, name='client_invoice_detail'),
    path('client-invoices/<uuid:pk>/edit/', views_client_invoices.client_invoice_edit_view, name='client_invoice_edit'),
    path('client-invoices/<uuid:pk>/delete/', views_client_invoices.client_invoice_delete_view, name='client_invoice_delete'),
    path('client-invoices/<uuid:pk>/status/', views_client_invoices.client_invoice_status_view, name='client_invoice_status'),
    path('client-invoices/<uuid:pk>/print/', views_client_invoices.client_invoice_print_view, name='client_invoice_print'),

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
