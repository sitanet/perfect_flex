from django.urls import path
from . import views

urlpatterns = [
    path('company_list/', views.company_list, name='company_list'),
    path('<int:pk>/', views.company_detail, name='company_detail'),
    path('create_company/', views.create_company, name='create_company'),
    path('company/update/<int:company_id>/', views.update_company, name='update_company'),
    path('<int:id>/delete/', views.company_delete, name='company_delete'),
    path('session_mgt/<int:company_id>/update/', views.session_mgt, name='session_mgt'),
]
