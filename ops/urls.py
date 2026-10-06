from django.urls import path
from . import views, views_work

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

    # Logout
    path('logout/', views.logout_view, name='logout'),
]
