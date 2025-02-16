"""
URL configuration for chart_of_account project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# chartofaccounts_project/urls.py
from django.contrib import admin
from django.urls import path, include

from profit_solutions import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts_admin/', include('accounts_admin.urls')),
    path('company/', include('company.urls')),
    path('accounts/', include('accounts.urls')),
    path('customers/', include('customers.urls')),
    path('transactions/', include('transactions.urls')),
    path('end_of_periods/', include('end_of_periods.urls')),
    path('loans/', include('loans.urls')),
    path('reports/', include('reports.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
