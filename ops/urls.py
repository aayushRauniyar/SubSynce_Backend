from django.urls import path
from . import views

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

    # Logout
    path('logout/', views.logout_view, name='logout'),
]
