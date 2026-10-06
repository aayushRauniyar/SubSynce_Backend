from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST, require_http_methods

from django.db import IntegrityError
from django.utils.http import url_has_allowed_host_and_scheme

from client.model.clientmanage import Client
from invoice.model.invoicemanagement import ContractorInvoice
from ops import services
from ops.access import STAFF_ROLES, forbidden, is_contractor, is_staff_user
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
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect('ops:dashboard')
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
    Dashboard - staff see business totals, contractors see their own jobs.

    Staff can narrow the figures with ?start=YYYY-MM-DD&end=YYYY-MM-DD.
    """
    user = request.user
    if is_contractor(user):
        return render(request, 'ops/dashboard_contractor.html', {
            'summary': services.contractor_summary(user),
        })
    if not is_staff_user(user):
        return forbidden(request)

    start = services.parse_date(request.GET.get('start'))
    end = services.parse_date(request.GET.get('end'))
    range_error = None
    if start and end and start > end:
        range_error = 'Start date must be on or before the end date.'
        start = end = None

    pending_invoices = (
        ContractorInvoice.objects.filter(status='PENDING')
        .select_related('site', 'created_by')
        .order_by('invoice_date')[:5]
    )
    context = {
        'summary': services.admin_summary(start, end),
        'today_jobs': services.todays_schedule(),
        'pending_invoices': pending_invoices,
        'start': start,
        'end': end,
        'range_error': range_error,
    }
    return render(request, 'ops/dashboard.html', context)


def _is_admin(request):
    # The Owner is the superuser, so they get every administrator screen too.
    return request.user.is_authenticated and request.user.role in STAFF_ROLES


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
@require_http_methods(['GET', 'POST'])
def client_create_view(request):
    if not _is_admin(request):
        messages.error(request, 'Only administrators can manage clients.')
        return redirect('ops:dashboard')

    if request.method == 'GET':
        return render(request, 'ops/client_add.html', {'user': request.user, 'form': ClientForm()})

    form = ClientForm(request.POST, request.FILES)
    if form.is_valid():
        email = form.cleaned_data.get('email')
        if email and Client.objects.filter(email=email).exists():
            form.add_error('email', 'A client with this email already exists.')
            return render(request, 'ops/client_add.html', {'user': request.user, 'form': form})
        try:
            form.save()
        except IntegrityError:
            # Deleted clients are soft-deleted, so their phone number still
            # occupies the unique index even though the form can't see them.
            form.add_error('phone', 'This phone number belongs to a removed client. Use a different number.')
            return render(request, 'ops/client_add.html', {'user': request.user, 'form': form})
        messages.success(request, 'Client added successfully.')
        return redirect('ops:clients')

    messages.error(request, 'Could not add client. Please check the details and try again.')
    return render(request, 'ops/client_add.html', {'user': request.user, 'form': form})


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

    form = ClientForm(request.POST, request.FILES, instance=client)
    if form.is_valid():
        phone = form.cleaned_data.get('phone')
        if phone and Client.objects.filter(phone=phone).exclude(id=pk).exists():
            messages.error(request, 'A client with this phone number already exists.')
            return redirect('ops:clients')
        try:
            form.save()
        except IntegrityError:
            messages.error(request, 'This phone number belongs to a removed client. Use a different number.')
            return redirect('ops:clients')
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
