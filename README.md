# SubSync Backend - Comprehensive Documentation

## Phase Status: Login & Authentication System (Merged)

**Branch:** `merging_login`  
**Date:** September 2026  
**Status:** ✅ Complete and Tested

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Decision: Hybrid Approach](#architecture-decision)
3. [Phase 1: What We Built](#phase-1-what-we-built)
4. [File Structure & Purpose](#file-structure)
5. [Detailed File-by-File Explanation](#file-explanations)
6. [Setup Instructions](#setup)
7. [Testing the Login System](#testing)
8. [Change Log](#change-log)
9. [References](#references)
10. [Next Phases](#next-phases)

---

## 🎯 Project Overview

**SubSync** is a cleaning management platform that connects:
- **Owners** (business owners)
- **Administrators** (managers)
- **Contractors/Subcontractors** (cleaning workers)

**Core Features:**
- Client and Site management
- Schedule and job tracking
- Invoice generation and payment tracking
- Compliance document management
- Profitability reporting

**Current Phase:** User authentication (login/logout) with session-based web interface

---

## 🏗️ Architecture Decision: Why Hybrid Approach?

### The Problem

We had **two conflicting specifications**:

1. **GitHub Backend** (existing code):
   - Django REST Framework (DRF) with JWT tokens
   - Multi-app structure (`authuser`, `client`)
   - API-first design (JSON responses)
   - Built for mobile/future React SPA

2. **techstack.md** (project requirements):
   - Django templates with Tailwind CSS
   - Session-based authentication
   - Single `ops` app
   - Server-rendered HTML

### The Solution: Option C (Hybrid)

We chose to **keep the existing GitHub backend** AND **add a new template layer** alongside it.

**Why?**
- ✅ Preserves all existing API code (no breaking changes)
- ✅ Matches techstack.md for web frontend
- ✅ Enables both web and mobile access
- ✅ Future-proof (can add React SPA later)

### How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    Browser / Mobile                      │
─────────────────────┬───────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────▼────┐              ┌─────▼────┐
    │  Web    │              │   API    │
    │ (ops)   │              │ (DRF)    │
    │         │              │          │
    │ Session │              │   JWT    │
    │  Auth   │              │  Auth    │
    │         │              │          │
    │ HTML    │              │  JSON    │
    │Response │              │ Response │
    └────┬────              └─────┬────
         │                         │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │    Django Core          │
         │    (settings.py)        │
         │                         │
         │  AUTH_USER_MODEL =      │
         │  'authuser.User'        │
         └────────────┬────────────┘
                      │
         ┌────────────▼────────────┐
         │      Database           │
         │    (db.sqlite3)         │
         │                         │
         │  POC_USER               │
         │  POC_CLIENT             │
         │  POC_SITE               │
         └─────────────────────────
```

**Key Insight:** Both `ops` (web) and `authuser`/`client` (API) share:
- The same database
- The same User model
- The same authentication system
- Different response formats (HTML vs JSON)

---

##  Phase 1: What We Built

### Features Implemented

1. ✅ **Login Page** (`/`)
   - Username/password form
   - Session-based authentication
   - Error handling with messages
   - Demo credentials display

2. ✅ **Dashboard** (`/dashboard/`)
   - Role-based navigation (Owner/Admin/Contractor see different menus)
   - Stats cards (active jobs, subcontractors, invoices, revenue)
   - User profile display
   - Logout button

3. ✅ **Logout** (`/logout/`)
   - Session termination
   - Redirect to login
   - Success message

4. ✅ **Authentication Flow**
   - `@login_required` decorator protects dashboard
   - Automatic redirect to login if not authenticated
   - Session cookies for persistence
   - CSRF protection on all forms

5. ✅ **Design System**
   - Tailwind CSS with SubSync brand colors
   - Material Symbols icons
   - Pretendard font
   - Responsive layout

---

## 📁 File Structure

```
SubSynce_Backend/
│
├── core/                          # Project configuration
│   ├── settings.py                # ← MODIFIED: Added ops app, templates, static, auth settings
│   └── urls.py                    # ← MODIFIED: Added web frontend URLs
│
├── authuser/                      # Existing API app (UNCHANGED)
│   ├── api/
│   │   ├── views/                 # API views (return JSON)
│   │   ── urls/                  # API routes (/api/v1/...)
│   ├── model/
│   │   └── user.py                # User model definition
│   └── models.py                  # Exports User model
│
├── client/                        # Existing API app (UNCHANGED)
│   ├── api/
│   │   ├── views/                 # API views (return JSON)
│   │   └── urls/                  # API routes
│   └── model/
│       └── clientmanage.py        # Client & Site models
│
├── ops/                           # ← NEW: Web template app
│   ├── __init__.py                # Makes ops a Python package
│   ├── admin.py                   # Django admin (empty for now)
│   ├── apps.py                    # App configuration
│   ├── models.py                  # Models (empty, uses authuser.User)
│   ├── tests.py                   # Tests (empty for now)
│   ├── views.py                   # ← NEW: Login, logout, dashboard views
│   ├── urls.py                    # ← NEW: URL routes for web pages
│   ├── migrations/
│   │   └── __init__.py            # Migrations folder
│   ├── templates/
│   │   ├── base.html              # ← NEW: Base template (shared layout)
│   │   └── ops/
│   │       ├── login.html         # ← NEW: Login page
│   │       └── dashboard.html     # ← NEW: Dashboard page
│   └── static/
│       └── css/
│           └── app.css            # ← NEW: Custom CSS styles
│
├── manage.py                      # Django command center
├── requirements.txt               # Python packages
└── README.md                      # ← THIS FILE (updated)
```

---

## 📝 Detailed File-by-File Explanation

### 1. **`core/settings.py`** (MODIFIED)

**Why Modified:** To integrate the new `ops` app with the existing project.

**Changes Made:**

#### a) Added `ops` to `INSTALLED_APPS`
```python
INSTALLED_APPS = [
    ...
    'authuser',
    'client',
    'ops',  # ← ADDED
]
```
**Why:** Django needs to know about the `ops` app to use its views, templates, and static files.

#### b) Updated `TEMPLATES` setting
```python
TEMPLATES = [
    {
        'DIRS': [BASE_DIR / 'ops' / 'templates'],  # ← ADDED
        ...
    },
]
```
**Why:** Tells Django where to find HTML templates. Without this, Django can't find `login.html` or `dashboard.html`.

#### c) Added `STATICFILES_DIRS`
```python
STATICFILES_DIRS = [
    BASE_DIR / 'ops' / 'static',  # ← ADDED
]
```
**Why:** Tells Django where to find CSS files. Without this, `app.css` won't load.

#### d) Added Authentication Settings
```python
LOGIN_URL = 'ops:login'                    # ← ADDED
LOGIN_REDIRECT_URL = 'ops:dashboard'       # ← ADDED
LOGOUT_REDIRECT_URL = 'ops:login'          # ← ADDED
```
**Why:**
- `LOGIN_URL`: Where to redirect unauthenticated users (when `@login_required` is used)
- `LOGIN_REDIRECT_URL`: Where to redirect after successful login
- `LOGOUT_REDIRECT_URL`: Where to redirect after logout

---

### 2. **`core/urls.py`** (MODIFIED)

**Why Modified:** To route web requests to the `ops` app.

**Changes Made:**

```python
# BEFORE:
basepatterns = [
    path("api/schema/", ...),
    path("api/", include("authuser.urls")),
    path("api/", include("client.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(basepatterns)),
]
```

```python
# AFTER:
# Web frontend URLs (template-based views)
web_patterns = [
    path("", include("ops.urls")),  # ← ADDED
]

# API URLs (DRF views)
api_patterns = [
    path("api/schema/", ...),
    path("api/", include("authuser.urls")),
    path("api/", include("client.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(web_patterns)),    # ← ADDED: Web routes
    path("", include(api_patterns)),    # ← KEPT: API routes
]
```

**Why:** 
- Web URLs (like `/dashboard/`) are handled by `ops.urls`
- API URLs (like `/api/v1/user/login/`) are handled by `authuser.urls`
- Both can coexist without conflicts

---

### 3. **`ops/__init__.py`** (NEW - EMPTY FILE)

**Why Created:** Makes `ops` a Python package.

**What It Does:**
- Empty file (no code)
- Tells Python "this folder is a module that can be imported"
- Required by Django to recognize the app

**Analogy:** Like a sign on a door that says "This is an office, not a storage room"

---

### 4. **`ops/apps.py`** (NEW)

**Why Created:** Registers the app with Django.

**Content:**
```python
from django.apps import AppConfig

class OpsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ops'
```

**What It Does:**
- `name = 'ops'` - Tells Django "my app name is ops"
- `default_auto_field` - Specifies the default primary key type for models

**Why Needed:** Django uses this to load the app and its components.

---

### 5. **`ops/admin.py`** (NEW - EMPTY)

**Why Created:** Required by Django app structure.

**Content:**
```python
from django.contrib import admin
# Register your models here.
```

**What It Does:**
- Empty for now (we don't have models in `ops` yet)
- Will be used later to register models for Django admin panel

**Why Needed:** Django expects this file in every app.

---

### 6. **`ops/models.py`** (NEW - EMPTY)

**Why Created:** Required by Django app structure.

**Content:**
```python
from django.db import models
# Create your models here.
```

**What It Does:**
- Empty for now (we use `authuser.User` model instead)
- Will be used later if we need app-specific models

**Why Needed:** Django expects this file in every app.

---

### 7. **`ops/tests.py`** (NEW - EMPTY)

**Why Created:** Required by Django app structure.

**Content:**
```python
from django.test import TestCase
# Create your tests here.
```

**What It Does:**
- Empty for now
- Will be used to write tests for views

**Why Needed:** Django expects this file in every app.

---

### 8. **`ops/views.py`** (NEW)

**Why Created:** Contains the logic for login, logout, and dashboard.

**Content:**
```python
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def login_view(request):
    """
    Login view - handles user authentication with Django sessions
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
            
            # Redirect to dashboard
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
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('ops:login')


@login_required
def dashboard_view(request):
    """
    Dashboard view - shows overview of the system
    Only authenticated users can access this page
    """
    context = {
        'user': request.user,
        'stats': {
            'active_jobs': 12,
            'subcontractors': 28,
            'invoices': 45,
            'revenue': 124500,
        }
    }
    
    return render(request, 'ops/dashboard.html', context)
```

**What Each Function Does:**

#### `login_view(request)`
- **Purpose:** Handles login form display and processing
- **GET request:** Shows the login form (`login.html`)
- **POST request:** 
  1. Gets username and password from form
  2. Calls `authenticate()` to check credentials against database
  3. If correct: Creates session, redirects to dashboard
  4. If wrong: Shows error message
- **Already logged in:** Redirects to dashboard (prevents re-login)

**Why Uses `authenticate()`:** This function uses `authuser.User` model automatically (because of `AUTH_USER_MODEL` setting in `settings.py`)

#### `logout_view(request)`
- **Purpose:** Ends user session
- **What it does:**
  1. Calls `logout()` to clear session
  2. Shows success message
  3. Redirects to login page

#### `dashboard_view(request)`
- **Purpose:** Shows the main dashboard
- **`@login_required` decorator:** Ensures only logged-in users can access
- **What it does:**
  1. Gets user info from `request.user` (this is `authuser.User` object)
  2. Creates context data (mock stats for now)
  3. Renders `dashboard.html` with context

**Why Uses `@login_required`:** Protects the page. If user is not logged in, Django automatically redirects to `LOGIN_URL` (which is `ops:login`)

---

### 9. **`ops/urls.py`** (NEW)

**Why Created:** Maps URLs to view functions.

**Content:**
```python
from django.urls import path
from . import views

# App namespace
app_name = 'ops'

urlpatterns = [
    # Login page (root URL)
    path('', views.login_view, name='login'),
    
    # Dashboard (protected - requires login)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Logout
    path('logout/', views.logout_view, name='logout'),
]
```

**What Each URL Does:**

| URL | View | Name | Purpose |
|---|---|---|---|
| `/` | `login_view` | `login` | Shows login form |
| `/dashboard/` | `dashboard_view` | `dashboard` | Shows dashboard (protected) |
| `/logout/` | `logout_view` | `logout` | Logs user out |

**Why `app_name = 'ops'`:** 
- Creates a namespace for URL names
- Allows us to use `{% url 'ops:login' %}` in templates
- Prevents naming conflicts with other apps

**How Templates Use This:**
```html
<a href="{% url 'ops:login' %}">Login</a>
<a href="{% url 'ops:dashboard' %}">Dashboard</a>
<a href="{% url 'ops:logout' %}">Logout</a>
```

---

### 10. **`ops/migrations/__init__.py`** (NEW - EMPTY FILE)

**Why Created:** Makes `migrations` a Python package.

**What It Does:**
- Empty file
- Tells Django this folder contains migration files
- Required for Django to track database changes

**Why Needed:** Even if we don't have models yet, Django expects this folder.

---

### 11. **`ops/templates/base.html`** (NEW)

**Why Created:** Shared layout for all pages.

**Content:** (Full HTML with Tailwind CSS config, fonts, messages area, and `{% block %}` tags)

**What It Does:**

#### a) **HTML Head Section**
```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SubSync{% endblock %}</title>
    
    <!-- Fonts -->
    <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/..." rel="stylesheet">
    
    <!-- Icons -->
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined..." rel="stylesheet">
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- Tailwind Config -->
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        surface: '#F5F3F1',
                        primary: '#F4842B',
                        ...
                    }
                }
            }
        }
    </script>
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{% static 'css/app.css' %}">
</head>
```

**Why This Section:**
- Loads Pretendard font (from design.md)
- Loads Material Symbols icons (from design.md)
- Loads Tailwind CSS (for styling)
- Configures Tailwind with SubSync brand colors
- Loads custom CSS for icon styling

#### b) **Body Section**
```html
<body class="bg-surface text-ink font-sans min-h-screen">
    
    <!-- Messages Area -->
    {% if messages %}
    <div class="fixed top-4 right-4 z-50 space-y-2">
        {% for message in messages %}
        <div class="px-4 py-3 rounded-xl shadow-lg ...">
            {{ message }}
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Main Content -->
    {% block content %}
    {% endblock %}
    
    <!-- Auto-hide messages -->
    <script>...</script>
</body>
```

**Why This Section:**
- `bg-surface text-ink` - Applies brand colors
- `{% if messages %}` - Shows success/error messages from views
- `{% block content %}` - Placeholder for child templates to fill
- JavaScript - Auto-hides messages after 5 seconds

**How Child Templates Use It:**
```html
{% extends 'base.html' %}

{% block title %}Login - SubSync{% endblock %}

{% block content %}
    <!-- Your page content here -->
{% endblock %}
```

---

### 12. **`ops/templates/ops/login.html`** (NEW)

**Why Created:** The login page that users see.

**Content:** (Full HTML with login form)

**What It Does:**

#### a) **Template Inheritance**
```html
{% extends 'base.html' %}
```
**Why:** Inherits the base layout (fonts, styles, messages area)

#### b) **Title Block**
```html
{% block title %}Login - SubSync{% endblock %}
```
**Why:** Sets the page title (shown in browser tab)

#### c) **Content Block**
```html
{% block content %}
<div class="min-h-screen flex items-center justify-center px-4 py-12">
    ...
</div>
{% endblock %}
```
**Why:** Fills in the main content area of `base.html`

#### d) **Login Form**
```html
<form method="post" action="{% url 'ops:login' %}" class="space-y-5">
    {% csrf_token %}
    
    <input type="text" name="username" required>
    <input type="password" name="password" required>
    
    <button type="submit">Sign In</button>
</form>
```

**Why Each Part:**

- **`method="post"`**: Sends data securely (not in URL)
- **`action="{% url 'ops:login' %}"`**: Sends to login view
- **`{% csrf_token %}`**: Security token (prevents CSRF attacks)
- **`name="username"`**: Must match what `login_view` expects (`request.POST.get('username')`)
- **`name="password"`**: Must match what `login_view` expects (`request.POST.get('password')`)
- **`required`**: HTML5 validation (field must be filled)

#### e) **Demo Credentials Display**
```html
<div class="mt-6 pt-6 border-t border-surface-container">
    <p class="text-xs text-ink-light text-center mb-3">Demo Credentials:</p>
    <div class="space-y-2 text-xs">
        <div class="flex justify-between items-center p-2 rounded-lg bg-surface">
            <span class="text-ink-light">Owner:</span>
            <code class="text-ink font-mono">testowner / Test@12345</code>
        </div>
        ...
    </div>
</div>
```
**Why:** Shows test credentials for easy login during development

---

### 13. **`ops/templates/ops/dashboard.html`** (NEW)

**Why Created:** The main dashboard page after login.

**Content:** (Full HTML with stats cards and logout button)

**What It Does:**

#### a) **Template Inheritance**
```html
{% extends 'base.html' %}
```
**Why:** Inherits base layout

#### b) **Header with Logout**
```html
<div class="flex justify-between items-center mb-8">
    <div>
        <h1 class="text-3xl font-bold text-ink">
            Welcome, {{ user.username }}! 👋
        </h1>
        <p class="text-ink-light mt-2">Role: {{ user.role }}</p>
    </div>
    <a href="{% url 'ops:logout' %}" 
       class="bg-primary text-on-primary px-4 py-2 rounded-xl hover:bg-primary-hover transition-colors flex items-center gap-2">
        <span class="material-symbols-outlined">logout</span>
        Logout
    </a>
</div>
```

**Why Each Part:**

- **`{{ user.username }}`**: Displays username from `authuser.User` model
- **`{{ user.role }}`**: Displays role (OWNER, ADMINISTRATOR, CONTRACTOR)
- **`{% url 'ops:logout' %}`**: Link to logout view
- **`bg-primary text-on-primary`**: Orange button with white text (SubSync brand)
- **`material-symbols-outlined`**: Logout icon from Material Symbols

#### c) **Stats Grid**
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
    <!-- Active Jobs -->
    <div class="bg-white rounded-2xl p-6 border border-surface-container">
        <div class="flex items-center justify-between mb-4">
            <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <span class="material-symbols-outlined text-primary">work</span>
            </div>
        </div>
        <p class="text-3xl font-bold text-ink">{{ stats.active_jobs }}</p>
        <p class="text-sm text-ink-light mt-1">Active Jobs</p>
    </div>
    ...
</div>
```

**Why Each Part:**

- **`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4`**: Responsive grid (1 column on mobile, 2 on tablet, 4 on desktop)
- **`bg-white rounded-2xl p-6 border border-surface-container`**: White card with rounded corners and border
- **`{{ stats.active_jobs }}`**: Displays number from context (currently mock data)
- **`material-symbols-outlined`**: Icon (work, person, receipt_long, trending_up)

#### d) **Context Data**
The template receives this data from `dashboard_view`:
```python
context = {
    'user': request.user,  # authuser.User object
    'stats': {
        'active_jobs': 12,
        'subcontractors': 28,
        'invoices': 45,
        'revenue': 124500,
    }
}
```

**Why:** Template uses `{{ stats.active_jobs }}` to display the number

---

### 14. **`ops/static/css/app.css`** (NEW)

**Why Created:** Custom CSS for icons and scrollbar styling.

**Content:**
```css
/* Material Symbols styling */
.material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-weight: normal;
    font-style: normal;
    font-size: 24px;
    line-height: 1;
    ...
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #F5F3F1;
}

::-webkit-scrollbar-thumb {
    background: #D9D3CC;
    border-radius: 4px;
}
```

**What It Does:**

#### a) **Material Symbols Styling**
- Sets font family to Material Symbols
- Defines default size (24px)
- Ensures icons render correctly

**Why Needed:** Without this, Material Symbols icons won't display properly

#### b) **Custom Scrollbar**
- Styles the scrollbar to match SubSync design
- Uses brand colors (#F5F3F1 for track, #D9D3CC for thumb)

**Why Needed:** Default browser scrollbars don't match the design

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.11 or 3.12
- Git
- VS Code (recommended)
- Internet connection (for Tailwind CDN)

### Step 1: Clone the Repository

```bash
git clone https://github.com/aayushRauniyar/SubSynce_Backend.git
cd SubSynce_Backend
```

### Step 2: Create Virtual Environment

**Windows (PowerShell):**
# SubSync Backend

SubSync is a Django REST API for managing cleaning businesses.

The system manages:

- Users and roles
- Clients and cleaning sites
- Contractor assignments
- Cleaning schedules
- Completed cleaning work
- Contractor invoices
- Client invoices
- Revenue, expenditure, profit, and dashboards

## Requirements

- Python 3.12 or later
- Windows PowerShell
- Git

## Setup

Open PowerShell in the backend directory:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**You'll know it worked when** you see `(venv)` at the start of your terminal line.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**What this installs:**
- Django 5.2.9 (downgraded from 6.0.3 for Python 3.11 compatibility)
- Django REST Framework
- SimpleJWT
- django-cors-headers
- drf-spectacular
- python-decouple
- And more...

### Step 4: Create `.env` File

Create a file named `.env` in the project root:

```env
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ACCESS_TOKEN_LIFETIME_HRS=4
JWT_REFRESH_TOKEN_LIFETIME_HRS=48
JWT_KEY=your-jwt-secret-key-change-this
PASSWORD_MIN_LENGTH=8
THROTTLE_RATES_IN_DAYS=1000000
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

Do not use development secrets in production. Keep real secrets out of source control.

## Database

After activating the virtual environment, run:

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Create a Django admin user when needed:

```powershell
python manage.py createsuperuser
```

## Run the API

```powershell
python manage.py migrate
```

The API is available at `http://127.0.0.1:8000/`.

## API Documentation

- Swagger UI: `http://127.0.0.1:8000/api/swagger/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`

## Main API Groups

- `/api/v1/admin/`
- `/api/v1/owner/`
- `/api/v1/user/`

Most endpoints require a JWT access token:

```text
Authorization: Bearer <access-token>
```

## Important Endpoints

### Contractor

- `/api/v1/user/schedule/` - View assigned schedules
- `/api/v1/user/clock-in/` - Start scheduled work
- `/api/v1/user/clock-out/<id>/` - Complete work
- `/api/v1/user/invoices/` - Submit and view contractor invoices
- `/api/v1/user/dashboard/` - View the contractor dashboard

### Administrator

- `/api/v1/admin/client/` - Manage clients
- `/api/v1/admin/site/` - Manage sites
- `/api/v1/admin/schedule/` - Manage schedules
- `/api/v1/admin/work/` - Review completed work
- `/api/v1/admin/invoices/` - Review contractor invoices
- `/api/v1/admin/client-invoice/` - Manage client invoices
- `/api/v1/admin/dashboard/` - View the administrator dashboard

Dashboard date filters use:

```text
?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

## User Roles

The application supports these roles:

- `OWNER`
- `ADMINISTRATOR`
- `CONTRACTOR`

Role permissions are enforced by the API. An owner can create administrators or contractors. An administrator can create contractors. Contractors cannot create accounts.

## Common Commands

```bash
# Run server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Open Python shell
python manage.py shell

# Create superuser
python manage.py createsuperuser

# Collect static files (for production)
python manage.py collectstatic

# Run tests
python manage.py test

# Show migrations
python manage.py showmigrations
```

### Common Template Tags

```html
{% url 'ops:login' %}           <!-- Generate URL -->
{% static 'css/app.css' %}      <!-- Static file URL -->
{% if user.is_authenticated %}  <!-- Check if logged in -->
{% for item in items %}         <!-- Loop -->
{% extends 'base.html' %}       <!-- Inherit template -->
{% block content %}             <!-- Define block -->
{% csrf_token %}                <!-- CSRF token -->
{{ user.username }}             <!-- Display variable -->
{{ stats.active_jobs }}         <!-- Display number -->
```

### Common View Patterns

```python
# Render template
return render(request, 'ops/page.html', context)

# Redirect
return redirect('ops:dashboard')

# Get form data
username = request.POST.get('username')

# Check if logged in
if request.user.is_authenticated:

# Add message
messages.success(request, 'Success!')
messages.error(request, 'Error!')

# Protected view
@login_required
def my_view(request):
    ...
```

---

##  Learning Resources

### Django
- Official Docs: https://docs.djangoproject.com/
- Django Tutorial: https://docs.djangoproject.com/en/stable/intro/tutorial01/
- Django Templates: https://docs.djangoproject.com/en/stable/ref/templates/

### Tailwind CSS
- Docs: https://tailwindcss.com/docs
- Play CDN: https://tailwindcss.com/docs/installation/play-cdn

### Material Symbols
- Icons: https://fonts.google.com/icons
- Usage: https://developers.google.com/fonts/docs/material_symbols

### Project Docs
- design.md: Frontend design specifications
- techstack.md: Technology stack decisions
- PRD.md: Product requirements

---

## 📞 Support

For questions or issues:
1. Check this README first
2. Check Django documentation
3. Ask in team chat
4. Create an issue on GitHub

---

##  License

This project is part of the SubSync cleaning management platform.

---

**Last Updated:** September 3, 2026  
**Phase:** Login & Authentication System ✅ Complete  
**Next Phase:** Client Management (In Progress)
