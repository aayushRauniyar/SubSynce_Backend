from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST

from client.model.clientmanage import Client
from ops.forms import ClientForm


def login_view(request):
    """
    Login view - handles user authentication with Django sessions
    
    GET: Shows the login form
    POST: Processes the login form
    """
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('ops:dashboard')
    
    # Handle POST request (form submission)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user against the database
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login successful - create session
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to dashboard (or next page if specified)
            next_url = request.GET.get('next', 'ops:dashboard')
            return redirect(next_url)
        else:
            # Login failed
            messages.error(request, 'Invalid username or password.')
    
    # Handle GET request (show login form)
    return render(request, 'ops/login.html')


def logout_view(request):
    """
    Logout view - ends user session and redirects to login
    
    This view logs out the user, clears the session, and redirects to login page
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('ops:login')


@login_required
def dashboard_view(request):
    """
    Dashboard view - shows overview of the system
    
    This view is protected by @login_required decorator
    Only authenticated users can access this page
    """
    # Get user information
    user = request.user
    
    # For now, we'll use mock data
    # Later, we'll fetch real data from the database
    context = {
        'user': user,
        'stats': {
            'active_jobs': 12,
            'subcontractors': 28,
            'invoices': 45,
            'revenue': 124500,
        }
    }
    
    return render(request, 'ops/dashboard.html', context)


def _is_admin(request):
    return request.user.is_authenticated and request.user.role == 'ADMINISTRATOR'


@login_required
def clients_view(request):
    """
    Clients list page - Administrator only.

    Supports search (?q=) across name/phone/email and pagination (?page=).
    """
    if not _is_admin(request):
        messages.error(request, 'Only administrators can access client management.')
        return redirect('ops:dashboard')

    query = request.GET.get('q', '').strip()
    clients = Client.objects.all().prefetch_related('sites').order_by('-created_at')

    if query:
        clients = clients.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
        )

    paginator = Paginator(clients, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'user': request.user,
        'page_obj': page_obj,
        'query': query,
        'total_clients': paginator.count,
    }
    return render(request, 'ops/clients.html', context)


@login_required
@require_POST
def client_create_view(request):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage clients.')
        return redirect('ops:dashboard')

    form = ClientForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data.get('email')
        if email and Client.objects.filter(email=email).exists():
            messages.error(request, 'A client with this email already exists.')
            return redirect('ops:clients')
        form.save()
        messages.success(request, 'Client added successfully.')
    else:
        messages.error(request, 'Could not add client. Please check the details and try again.')

    return redirect('ops:clients')


@login_required
@require_POST
def client_update_view(request, pk):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage clients.')
        return redirect('ops:dashboard')

    client = Client.objects.filter(id=pk).first()
    if not client:
        messages.error(request, 'Client not found.')
        return redirect('ops:clients')

    form = ClientForm(request.POST, instance=client)
    if form.is_valid():
        phone = form.cleaned_data.get('phone')
        if phone and Client.objects.filter(phone=phone).exclude(id=pk).exists():
            messages.error(request, 'A client with this phone number already exists.')
            return redirect('ops:clients')
        form.save()
        messages.success(request, 'Client updated successfully.')
    else:
        messages.error(request, 'Could not update client. Please check the details and try again.')

    return redirect('ops:clients')


@login_required
@require_POST
def client_delete_view(request, pk):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage clients.')
        return redirect('ops:dashboard')

    client = Client.objects.filter(id=pk).first()
    if client:
        client.delete()
        messages.success(request, 'Client removed successfully.')
    else:
        messages.error(request, 'Client not found.')

    return redirect('ops:clients')
