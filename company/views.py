from django.shortcuts import render, get_object_or_404, redirect

from accounts.views import check_role_admin
from .models import Company
from .forms import CompanyForm, EndSession
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

# @login_required(login_url='login')
# @user_passes_test(check_role_admin)
def company_list(request):
    companies = Company.objects.all()
    return render(request, 'company/company_list.html', {'companies': companies})


# @login_required(login_url='login')
# @user_passes_test(check_role_admin)
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    return render(request, 'company/company_detail.html', {'company': company})



def create_company(request):
    if request.method == "POST":
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('company_list')  # Redirect to the company list page
    else:
        form = CompanyForm()
    return render(request, 'company/create_company.html', {'form': form})

# @login_required(login_url='login')
# @user_passes_test(check_role_admin)
def update_company(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    if request.method == "POST":
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('company_list')
    else:
        form = CompanyForm(instance=company)
    return render(request, 'company/update_company.html', {'form': form, 'company': company})


@login_required(login_url='login')
@user_passes_test(check_role_admin)
def company_delete(request, id):
    company = get_object_or_404(Company, id=id)
    if request.method == 'POST':
        company.delete()
        return redirect('company_list')
    return render(request, 'company/company_confirm_delete.html', {'company': company})



from .forms import EndSession

@login_required(login_url='login')
@user_passes_test(check_role_admin)
def session_mgt(request, company_id):
    company = Company.objects.get(pk=company_id)
    if request.method == 'POST':
        form = EndSession(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Session Change Successfully')
            return redirect('session_mgt', company_id=company.id)  # Redirect to company detail page
    else:
        form = EndSession(instance=company)
    
    return render(request, 'company/session_mgt.html', {'form': form})


