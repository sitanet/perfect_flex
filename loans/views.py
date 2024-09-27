from datetime import timedelta, timezone
from decimal import Decimal
import json
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import User
from accounts.views import check_role_admin
from accounts_admin.models import Account, Account_Officer
from company.models import Company
import customers
from django.db import transaction
from customers.models import Customer
from loans.forms import LoansForm, LoansApproval
from loans.models import LoanHist, Loans
from transactions.models import Memtrans
from django.db.models import Sum, Max
from django.contrib import messages
from django.utils import timezone



from transactions.utils import generate_loan_disbursement_id, generate_loan_repayment_id, generate_loan_written_off_id
from django.contrib.auth.decorators import login_required, user_passes_test
# Create your views here.

@login_required(login_url='login')
@user_passes_test(check_role_admin)
def loans(request):
    return render(request, 'loans/loans.html')





# list of account that can apply for loan
@login_required(login_url='login')
@user_passes_test(check_role_admin)
def choose_to_apply_loan(request):
    data = Memtrans.objects.all().order_by('-id').first()
    customers = Customer.objects.filter(label='L').order_by('-id')
    total_amounts = []
    for customer in customers:
        # Calculate the total amount for each customer
        total_amount = Memtrans.objects.filter(gl_no=customer.gl_no, ac_no=customer.ac_no, error='A').aggregate(total_amount=Sum('amount'))['total_amount']
        total_amounts.append({
            'customer': customer,
            'total_amount': total_amount or 0.0,
        })
    return render(request, 'loans/choose_to_apply_for_loan.html',{'customers':customers,'total_amounts':total_amounts,'data':data})


# loan application
from django.core.exceptions import ValidationError
from django.utils import timezone

@login_required(login_url='login')
@user_passes_test(check_role_admin)

def loan_application(request, id):
    customer = get_object_or_404(Customer, id=id)
    loan_account = Account.objects.filter(gl_no__startswith='104').exclude(gl_no='10400').exclude(gl_no='104100').exclude(gl_no='104200')
    initial_values = {'gl_no_cust': customer.gl_no, 'ac_no_cust': customer.ac_no}
    user = User.objects.get(id=request.user.id)
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''
    
    
    if company.session_status == 'Closed':
        
        return HttpResponse("You can not post any transaction. Session is closed.") 
    else:
        if request.method == 'POST':
            form = LoansForm(request.POST, request.FILES)
            if form.is_valid():
                gl_no = form.cleaned_data['gl_no']
                ac_no = form.cleaned_data['ac_no']
                
                with transaction.atomic():
                    # Check if there is an existing loan with the same 'gl_no' and 'ac_no'
                    existing_loan = Loans.objects.filter(gl_no=gl_no, ac_no=ac_no).last()

                    if existing_loan:
                        # If an existing loan is found, create a new loan with an incremented cycle
                        new_loan = Loans(
                            branch=form.cleaned_data.get('branch', 0),
                            appli_date=form.cleaned_data.get('appli_date', 0),
                            loan_amount=form.cleaned_data.get('loan_amount', 0),
                            interest_rate=form.cleaned_data.get('interest_rate', 0),
                            payment_freq=form.cleaned_data.get('payment_freq', 0),
                            interest_calculation_method=form.cleaned_data.get('interest_calculation_method', 0),
                            loan_officer=form.cleaned_data.get('loan_officer', 0),
                            business_sector=form.cleaned_data.get('business_sector', 0),
                            customer=customer,
                            gl_no=gl_no,
                            ac_no=ac_no,
                            
                            num_install=form.cleaned_data.get('num_install', 0),
                            cycle=existing_loan.cycle + 1 if existing_loan.cycle is not None else 1,
                            # ... other fields ...
                        )
                    else:
                        # If no existing loan is found, create a new loan with cycle 1
                        new_loan = Loans(
                            branch=form.cleaned_data.get('branch', 0),
                            appli_date=form.cleaned_data.get('appli_date', 0),
                            loan_amount=form.cleaned_data.get('loan_amount', 0),
                            interest_rate=form.cleaned_data.get('interest_rate', 0),
                            payment_freq=form.cleaned_data.get('payment_freq', 0),
                            interest_calculation_method=form.cleaned_data.get('interest_calculation_method', 0),
                            loan_officer=form.cleaned_data.get('loan_officer', 0),
                            business_sector=form.cleaned_data.get('business_sector', 0),
                            customer=customer,
                            gl_no=gl_no,
                            ac_no=ac_no,
                            
                            num_install=form.cleaned_data.get('num_install', 0),
                            cycle=1,
                            # ... other fields ...
                        )

                    new_loan.save()
                    customer.loan = 'T'
                    customer.save()
                    print("Customer:", customer)  # Print the customer object for debugging

                    messages.success(request, 'Loan Applied successfully!')
                    return redirect('choose_to_apply_loan')
            
            else:
                messages.error(request, 'Form is not valid. Please check the entered data.')
        else:
            form = LoansForm(initial=initial_values)

    return render(request, 'loans/loans_application.html', {'form': form, 'customer': customer, 'loan_account': loan_account,'company':company, 'company_date':company_date})


@login_required(login_url='login')
@user_passes_test(check_role_admin)
def choose_to_modify_loan(request):
    # Filter loans with approval status 'F' or 'R'
    customers = Loans.objects.select_related('customer').filter(approval_status__in=['F', 'R'])

    return render(request, 'loans/choose_to_modify_loan.html', {'customers': customers})



@login_required(login_url='login')
@user_passes_test(check_role_admin)
def loan_modification(request, id):
    loan_instance = get_object_or_404(Loans, id=id)
    cust_data = Account.objects.filter(gl_no__startswith='200').exclude(gl_no='200100').exclude(gl_no='200200').exclude(gl_no='200000')
    gl_no_list = Account.objects.all().values_list('gl_no', flat=True).filter(gl_no__startswith='200')
    cust_branch = Company.objects.all()
    customers = loan_instance.customer
    officer = Account_Officer.objects.all()
    user = User.objects.get(id=request.user.id)
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''
    
    
    if company.session_status == 'Closed':
        
        return HttpResponse("You can not post any transaction. Session is closed.") 
    else:

        if request.method == 'POST':
            form = LoansModifyForm(request.POST, request.FILES, instance=loan_instance)
            if form.is_valid():
                form.instance.approval_status = 'F'
                form.save()
                messages.success(request, 'Loan modified successfully!')
                return redirect('choose_to_modify_loan')
        else:
            form = LoansModifyForm(instance=loan_instance)

    return render(request, 'loans/loan_application_modification.html', {
        'form': form,
        'loan_instance': loan_instance,
        'customers': customers,
        'cust_data': cust_data,
        'cust_branch': cust_branch,
        'gl_no_list': gl_no_list,
        'officer': officer,'company':company, 'company_date':company_date,
    })

   



@login_required(login_url='login')
@user_passes_test(check_role_admin)
def choose_loan_approval(request):
    # Filter customers with loan approval status set to 'F'
    customers = Loans.objects.select_related('customer').filter(approval_status='F')
    for customer in customers:
        if customer.customer:
            print(customer.customer.first_name)
        else:
            print("No associated customer for this loan.")
    # Pass the customers data to the template
    return render(request, 'loans/choose_loan_approval.html', {'customers': customers})



@login_required(login_url='login')
@user_passes_test(check_role_admin)


def loan_approval(request, id):
    customer = get_object_or_404(Loans, id=id)
    cust_data = Account.objects.filter(gl_no__startswith='200').exclude(gl_no='200100').exclude(gl_no='200200').exclude(gl_no='200000')
    gl_no = Account.objects.all().values_list('gl_no', flat=True).filter(gl_no__startswith='200')
    cust_branch = Company.objects.all()
    customers = customer.customer
    officer = Account_Officer.objects.all()
    user = User.objects.get(id=request.user.id)
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    # Assuming 'loans' is an instance of a Django model
    if customer.appli_date:
        appli_date = customer.appli_date.strftime('%Y-%m-%d')
    else:
        appli_date = ''

    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''
    
    
    if company.session_status == 'Closed':
        
        return HttpResponse("You can not post any transaction. Session is closed.") 
    else:
        if request.method == 'POST':
            form = LoansApproval(request.POST, request.FILES, instance=customer)
            if form.is_valid():
                customer.approval_status = 'T'
                customer.save()
                form.save()

                messages.success(request, 'Loan Approved successfully!')
                return redirect('choose_loan_approval')
        else:
            initial_data = {'gl_no': customer.gl_no}
            form = LoansApproval(instance=customer, initial=initial_data)

    return render(request, 'loans/loan_approval.html', {
        'form': form,
        'customer': customer,
        'customers': customers,
        'cust_data': cust_data,
        'cust_branch': cust_branch,
        'gl_no': gl_no,
        'officer': officer,
        'appli_date':appli_date,
        'company_date':company_date,
    })



@login_required(login_url='login')
@user_passes_test(check_role_admin)
def reject_loan(request, id):
    customer = get_object_or_404(Loans, id=id)
    cust_data = Account.objects.filter(gl_no__startswith='200').exclude(gl_no='200100').exclude(gl_no='200200').exclude(gl_no='200000')
    gl_no = Account.objects.all().values_list('gl_no', flat=True).filter(gl_no__startswith='200')
    cust_branch = Company.objects.all()
    customers = customer.customer
 
    officer = Account_Officer.objects.all()
    if request.method == 'POST':
        form = LoansRejectForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            customer.approval_status= 'R'
            form.save()
            messages.success(request, 'Loan Approved successfully!')
            
            return redirect('choose_loan_approval')
    else:
        initial_data = {'gl_no': customer.gl_no}
        form = LoansRejectForm(instance=customer, initial=initial_data)
        # form = CustomerForm(instance=customer)
    return render(request, 'loans/reject_loan.html', {'form': form, 'customer': customer , 'customers': customers, 'cust_data': cust_data,
     'cust_branch': cust_branch, 'gl_no': gl_no, 'officer':officer})


@login_required(login_url='login')
@user_passes_test(check_role_admin)
def choose_approved_loan(request):
    customers = Loans.objects.filter(approval_status='T')
 
  
    return render(request, 'loans/choose_reverse_loan_approval.html', {'customers': customers})




@login_required(login_url='login')
@user_passes_test(check_role_admin)
def reverse_loan_approval(request, id):
    customer = get_object_or_404(Loans, id=id)
    cust_data = Account.objects.filter(gl_no__startswith='200').exclude(gl_no='200100').exclude(gl_no='200200').exclude(gl_no='200000')
    gl_no = Account.objects.all().values_list('gl_no', flat=True).filter(gl_no__startswith='200')
    cust_branch = Company.objects.all()
    customers = customer.customer
 
    officer = Account_Officer.objects.all()
    if request.method == 'POST':
        form = LoansModifyForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            customer.approval_status= 'F'
            form.save()
            messages.success(request, 'Approved Loan Reversal successfully!')
            
            return redirect('choose_approved_loan')
    else:
        initial_data = {'gl_no': customer.gl_no}
        form = LoansModifyForm(instance=customer, initial=initial_data)
        # form = CustomerForm(instance=customer)
    return render(request, 'loans/reverse_loan_approval.html', {'form': form, 'customer': customer , 'customers': customers, 'cust_data': cust_data,
     'cust_branch': cust_branch, 'gl_no': gl_no, 'officer':officer})



@login_required(login_url='login')
@user_passes_test(check_role_admin)
def choose_to_disburse(request):
    customers = Loans.objects.select_related('customer').filter(approval_status='T',disb_status='F')
    for customer in customers:
        if customer.customer:
            print(customer.customer.first_name)
        else:
            print("No associated customer for this loan.")
    # Pass the customers data to the template
    return render(request, 'loans/choose_to_disburse.html', {'customers': customers})


@login_required(login_url='login')
@user_passes_test(check_role_admin)
def loan_disbursement_reversal(request, id):
    customer = get_object_or_404(Loans, id=id)
    account = get_object_or_404(Account, gl_no=customer.gl_no)

    # Access the related Customer instance
    customers = customer.customer
    cust_data = Account.objects.filter(gl_no__startswith='20').exclude(gl_no='20100').exclude(
        gl_no='20200').exclude(gl_no='20000')
    gl_no = Account.objects.all().values_list('gl_no', flat=True).filter(gl_no__startswith='200')

    ac_no_list = Memtrans.objects.filter(ac_no=customer.ac_no).values_list('ac_no', flat=True).distinct()
    cust_branch = Company.objects.all()
    amounts = Memtrans.objects.filter(ac_no=customer.ac_no, gl_no__startswith='2').values('gl_no').annotate(total_amount=Sum('amount')).order_by('-total_amount')
    officer = Account_Officer.objects.all()
    
    user = User.objects.get(id=request.user.id)
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''
    
    
    if company.session_status == 'Closed':
        
        return HttpResponse("You can not post any transaction. Session is closed.") 
    else:
        if request.method == 'POST':
            form = MemtransForm(request.POST, request.FILES, instance=customer)
            if form.is_valid():
                with transaction.atomic():
                    if account.int_to_recev_gl_dr is not None and account.int_to_recev_ac_dr is not None and account.unearned_int_inc_gl is not None and account.unearned_int_inc_ac is not None:
                        debit_transaction = Memtrans(
                            branch=customer.branch,
                            gl_no=customer.gl_no,
                            ac_no=customer.ac_no,
                            amount=-customer.loan_amount,
                            description='Loan Disbursement - Debit',
                            type='D',
                            ses_date=company_date,
                        )
                        debit_transaction.save()

                        unique_id = generate_loan_disbursement_id()
                        debit_transaction.trx_no = unique_id
                        debit_transaction.save()

                        credit_transaction = Memtrans(
                            branch=form.cleaned_data['branch'],
                            gl_no=form.cleaned_data['gl_no_cashier'],
                            ac_no=form.cleaned_data['ac_no_cashier'],
                            amount=customer.loan_amount,
                            description='Loan Disbursement - Credit',
                            error='A',
                            type='C',
                            ses_date=form.cleaned_data['ses_date']
                        )
                        credit_transaction.save()

                        credit_transaction.trx_no = debit_transaction.trx_no
                        credit_transaction.save()

                        #interest receive and unearned income
                    

                        # Calculate loan schedule
                        loan_schedule = customer.calculate_loan_schedule()
                        customer.disb_status = 'T'
                        customer.disbursement_date = form.cleaned_data['ses_date']
                        customer.save()

                        # Insert loan schedule into loanhist
                        for payment in loan_schedule:
                            loanhist_entry = LoanHist(
                                branch=customer.branch,
                                gl_no=customer.gl_no,
                                ac_no=customer.ac_no,
                                cycle=customer.cycle,
                                period=payment['period'],
                                trx_date=payment['payment_date'],
                                trx_type='LD',
                                principal=payment['principal_payment'],
                                interest=payment['interest_payment'],
                                penalty=0
                            )
                            loanhist_entry.save()

                            loanhist_entry.trx_no = debit_transaction.trx_no
                            loanhist_entry.save()

                            # Sum the interest from LoanHist
                            total_interest = LoanHist.objects.filter(gl_no=customers.gl_no, ac_no=customers.ac_no, cycle=customer.cycle).aggregate(total_interest=Sum('interest'))['total_interest']
                            total_interest = total_interest or 0  # Set to 0 if no interest records found

                            # Update loan_balance in Loans model
                            customer.total_loan = customer.loan_amount + total_interest
                            customer.total_interest = total_interest
                            customer.save()
                    
                        debit_transaction = Memtrans(
                            branch=customer.branch,
                            gl_no=account.int_to_recev_gl_dr,
                            ac_no=account.int_to_recev_ac_dr,
                            amount=-customer.total_interest,
                            description='Interest on Loan - Debit',
                            type='L',
                            ses_date=timezone.now()
                        )
                        debit_transaction.save()

                        unique_id = generate_loan_disbursement_id()
                        debit_transaction.trx_no = unique_id
                        debit_transaction.save()
                    
                        credit_transaction = Memtrans(
                            branch=form.cleaned_data['branch'],
                            gl_no=account.unearned_int_inc_gl,
                            ac_no=account.unearned_int_inc_ac,
                            amount=customer.total_interest,
                            description='Interest on Loan - Credit',
                        
                            type='L',
                            ses_date=timezone.now()
                        )
                        credit_transaction.save()

                        credit_transaction.trx_no = debit_transaction.trx_no
                        credit_transaction.save()
                        messages.success(request, 'Loan Disbursed successfully!')
                        return redirect('choose_to_disburse')
                    else:
                        messages.warning(request, 'Please Define all Required Loan Before Disbursement.')
                        return redirect('choose_to_disburse')

        else:
            initial_data = {'gl_no': customer.gl_no}
            form = LoansModifyForm(instance=customer, initial=initial_data)

    return render(request, 'loans/loan_disbursement.html', {
        'form': form,
        'customers': customers,
        'customer': customer,
        'cust_data': cust_data,
        'cust_branch': cust_branch,
        'gl_no': gl_no,
        'officer': officer,
        'ac_no_list': ac_no_list,
        'amounts': amounts,
        'account': account,'company':company, 'company_date':company_date,
    })

def choose_to_disburse(request):
    customers = Loans.objects.select_related('customer').filter(approval_status='T', disb_status='F')
    for customer in customers:
        if customer.customer:
            print(customer.customer.first_name)
        else:
            print("No associated customer for this loan.")
    # Pass the customers data to the template
    return render(request, 'loans/choose_to_disburse.html', {'customers': customers})

 # Assuming you have this utility function

@login_required(login_url='login')
@user_passes_test(check_role_admin)

def loan_disbursement(request, id):
    loan = get_object_or_404(Loans, id=id)
    account = get_object_or_404(Account, gl_no=loan.gl_no)
    customer = loan.customer  # Assuming loan.customer is a ForeignKey to Customer model
    
    cust_data = Account.objects.filter(gl_no__startswith='20').exclude(gl_no__in=['20100', '20200', '20000'])
    gl_no = Account.objects.filter(gl_no__startswith='200').values_list('gl_no', flat=True)
    ac_no_list = Memtrans.objects.filter(ac_no=loan.ac_no).values_list('ac_no', flat=True).distinct()
    cust_branch = Company.objects.all()
    amounts = Memtrans.objects.filter(ac_no=loan.ac_no, gl_no__startswith='2').values('gl_no').annotate(total_amount=Sum('amount')).order_by('-total_amount')
    officer = Account_Officer.objects.all()
    
    user = request.user
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''
    
    if loan.appli_date:
        appli_date = loan.appli_date.strftime('%Y-%m-%d')
    else:
        appli_date = ''
    
    if loan.approval_date:
        approve_date = loan.approval_date.strftime('%Y-%m-%d')
    else:
        approve_date = ''
    
    if company.session_status == 'Closed':
        return HttpResponse("You cannot post any transaction. Session is closed.")
    else:
        if request.method == 'POST':
            form = MemtransForm(request.POST, request.FILES)
            if form.is_valid():
                ses_date = form.cleaned_data['ses_date']
                disbursement_date = request.POST.get('disbursement_date')
              
                print(disbursement_date) 
                if ses_date > company.session_date:
                    messages.warning(request, 'Transaction date cannot be greater than the session date.')
                    return redirect('choose_to_disburse')
                
                customer_id = customer.id  # Assuming the customer ID is in the form data
                with transaction.atomic():
                    if account.int_to_recev_gl_dr and account.int_to_recev_ac_dr and account.unearned_int_inc_gl and account.unearned_int_inc_ac:
                        # Generate a unique transaction number
                        unique_trx_no = generate_loan_disbursement_id()

                        debit_transaction = Memtrans(
                            branch=loan.branch,
                            customer_id=customer_id,  # Use the customer ID from the form data
                            cycle=loan.cycle,
                            gl_no=loan.gl_no,
                            ac_no=loan.ac_no,
                            amount=-loan.loan_amount,
                            description='Loan Disbursement - Debit',
                            type='D',
                            account_type='L',
                            code='LD',
                            sys_date=timezone.now(),
                            ses_date=form.cleaned_data['ses_date'],
                            app_date=form.cleaned_data['app_date'],
                            trx_no=unique_trx_no,
                            user=request.user
                        )
                        debit_transaction.save()

                        credit_transaction = Memtrans(
                            branch=form.cleaned_data['branch'],
                            customer_id=customer_id,  # Use the customer ID from the form data
                            cycle=loan.cycle,
                            gl_no=form.cleaned_data['gl_no_cashier'],
                            ac_no=form.cleaned_data['ac_no_cashier'],
                            amount=loan.loan_amount,
                            description=f'{customer.first_name}, {customer.last_name}, {customer.gl_no}-{customer.ac_no}',
                            error='A',
                            type='C',
                            account_type='C',
                            code='LD',
                            sys_date=timezone.now(),
                            ses_date=form.cleaned_data['ses_date'],
                            app_date=form.cleaned_data['app_date'],
                            trx_no=unique_trx_no,
                            user=request.user
                        )
                        credit_transaction.save()

                        # Calculate loan schedule
                        loan_schedule = loan.calculate_loan_schedule()
                        loan.disb_status = 'T'
                        loan.cust_gl_no = form.cleaned_data['gl_no_cashier']
                        loan.disbursement_date = disbursement_date
                        print(f"Disbursement date to be saved: {loan.disbursement_date}") 
                        loan.save()

                        # Insert loan schedule into LoanHist
                        for payment in loan_schedule:
                            loanhist_entry = LoanHist(
                                branch=loan.branch,
                                gl_no=loan.gl_no,
                                ac_no=loan.ac_no,
                                cycle=loan.cycle,
                                period=payment['period'],
                                trx_date=payment['payment_date'],
                                trx_type='LD',
                                trx_naration='Repayment Due',
                                principal=payment['principal_payment'],
                                interest=payment['interest_payment'],
                                penalty=0,
                                trx_no=unique_trx_no
                            )
                            loanhist_entry.save()

                        # Sum the interest from LoanHist
                        total_interest = LoanHist.objects.filter(gl_no=loan.gl_no, ac_no=loan.ac_no, cycle=loan.cycle).aggregate(total_interest=Sum('interest'))['total_interest'] or 0

                        # Update loan balance in Loans model
                        loan.total_loan = loan.loan_amount + total_interest
                        loan.total_interest = total_interest
                        loan.save()

                        debit_transaction = Memtrans(
                            branch=loan.branch,
                            customer_id=customer_id,
                            cycle=loan.cycle,
                            gl_no=account.int_to_recev_gl_dr,
                            ac_no=account.int_to_recev_ac_dr,
                            amount=-loan.total_interest,
                            description=f'{customer.first_name}, {customer.last_name}, {customer.gl_no}-{customer.ac_no}, Total Interest',
                            type='D',
                            account_type='I',
                            code='LD',
                            sys_date=timezone.now(),
                            ses_date=form.cleaned_data['ses_date'],
                            app_date=form.cleaned_data['app_date'],
                            trx_no=unique_trx_no,
                            user=request.user
                        )
                        debit_transaction.save()

                        credit_transaction = Memtrans(
                            branch=form.cleaned_data['branch'],
                            customer_id=customer_id,
                            cycle=loan.cycle,
                            gl_no=account.unearned_int_inc_gl,
                            ac_no=account.unearned_int_inc_ac,
                            amount=loan.total_interest,
                            description=f'{customer.first_name}, {customer.last_name}, {customer.gl_no}-{customer.ac_no}, Total Interest on Loan - Credit',
                            type='C',
                            account_type='I',
                            code='LD',
                            sys_date=timezone.now(),
                            ses_date=form.cleaned_data['ses_date'],
                            app_date=form.cleaned_data['app_date'],
                            trx_no=unique_trx_no,
                            user=request.user
                        )
                        credit_transaction.save()

                        messages.success(request, 'Loan Disbursed successfully!')
                        return redirect('choose_to_disburse')
                    else:
                        messages.warning(request, 'Please define all required loan parameters before disbursement, check Loan Settings.')
                        return redirect('choose_to_disburse')
        else:
            initial_data = {'gl_no': loan.gl_no}
            form = LoansModifyForm(instance=loan, initial=initial_data)

    return render(request, 'loans/loan_disbursement.html', {
        'form': form,
        'customers': customer,
        'loan': loan,
        'customer': loan,
        'cust_data': cust_data,
        'cust_branch': cust_branch,
        'gl_no': gl_no,
        'officer': officer,
        'ac_no_list': ac_no_list,
        'amounts': amounts,
        'account': account,
        'company': company,
        'company_date': company_date,
        'appli_date':appli_date,
        'approve_date':approve_date,
    })





from django.db.models import Sum

@login_required(login_url='login')
@user_passes_test(check_role_admin)

def loan_schedule_view(request, loan_id):
    loan_instance = get_object_or_404(Loans, id=loan_id)
    loan_schedule = loan_instance.calculate_loan_schedule()
    customers = loan_instance.customer
    company = Company.objects.first()
    print(f"Loan Instance: {loan_id}")

    total_interest_sum = sum(payment['interest_payment'] for payment in loan_schedule)
    total_principal_sum = sum(payment['principal_payment'] for payment in loan_schedule)
    total_payments_sum = sum(payment['total_payment'] for payment in loan_schedule)
   


    context = {
        'loan_instance': loan_instance,
        'loan_schedule': loan_schedule,
        'total_interest_sum': total_interest_sum,
        'total_principal_sum': total_principal_sum,
        'total_payments_sum': total_payments_sum,
        'customers': customers,
        'company': company,
    
        
    }


  

    return render(request, 'loans/loan_schedule_template.html', context)








# views.py

from django.shortcuts import render
from .forms import LoanApplicationForm, LoanApplicationForm, LoansApproval, LoansChooseRepaymeny, LoansModifyForm, LoansRejectForm, MemtransForm
from .utils import calculate_loan_schedule # Create a utility function for calculating loan schedule


@login_required(login_url='login')
@user_passes_test(check_role_admin)
def loan_schedule_demo(request):
    if request.method == 'POST':
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            form.set_numerical_value()
            # Calculate loan schedule using form data
            loan_schedule = form.calculate_loan_schedule()

            # Pass form and loan_schedule to the context
            total_interest_sum = sum(payment['interest_payment'] for payment in loan_schedule)
            total_principal_sum = sum(payment['principal_payment'] for payment in loan_schedule)
            total_payments_sum = sum(payment['total_payment'] for payment in loan_schedule)

            context = {
                'form': form,
                'loan_schedule': loan_schedule,
                'total_interest_sum': total_interest_sum,
                'total_principal_sum': total_principal_sum,
                'total_payments_sum': total_payments_sum,
            }

            return render(request, 'loans/loan_schedule_demo.html', context)

    # If it's a GET request or the form is not valid, display an empty form
    form = LoanApplicationForm()
    context = {
        'form': form,
    }
    return render(request, 'loans/loan_schedule_form.html', context)




@login_required(login_url='login')
@user_passes_test(check_role_admin)
def choose_loan_repayment(request):
    # Filter customers with loan approval status set to 'F'
    customers = Loans.objects.select_related('customer').filter(total_loan__gt=0)
    
  
    # Pass the customers data to the template
    return render(request, 'loans/choose_loan_repayment.html', {'customers': customers})










from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Sum
from django.contrib import messages
from .forms import LoanHistForm
from company.models import Company



@login_required(login_url='login')
@user_passes_test(check_role_admin)  




def loan_repayment(request, id):
    customer = get_object_or_404(Loans, id=id)
    account = get_object_or_404(Account, gl_no=customer.gl_no)
    customers = customer.customer

    cust_data = Account.objects.filter(gl_no__startswith='20').exclude(gl_no__in=['20100', '20200', '20000'])
    gl_no = Account.objects.filter(gl_no__startswith='200').values_list('gl_no', flat=True)
    ac_no_list = Memtrans.objects.filter(ac_no=customer.ac_no).values_list('ac_no', flat=True).distinct()
    cust_branch = Company.objects.all()
    amounts = Memtrans.objects.filter(ac_no=customer.ac_no, gl_no__startswith='2').values('gl_no').annotate(total_amount=Sum('amount')).order_by('-total_amount')
    officer = Account_Officer.objects.all()

    user = User.objects.get(id=request.user.id)
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''
    
    total_principal_currently = LoanHist.objects.filter(trx_date__lt=company_date, gl_no=customer.gl_no, ac_no=customer.ac_no, cycle=customer.cycle).aggregate(Sum('principal'))['principal__sum'] or 0
    total_interest_currently = LoanHist.objects.filter(trx_date__lt=company_date, gl_no=customer.gl_no, ac_no=customer.ac_no, cycle=customer.cycle).aggregate(Sum('interest'))['interest__sum'] or 0

    # Sum the principal using gl_no, ac_no, and cycle
    total_principal = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle
    ).aggregate(Sum('principal'))['principal__sum'] or 0

    # Sum the interest using gl_no, ac_no, and cycle
    total_interest = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle
    ).aggregate(Sum('interest'))['interest__sum'] or 0

    # Sum the principal between disbursement and session date
    disbursement_date = customer.disbursement_date
    total_principal_between_dates = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle,
        trx_date__gte=disbursement_date,
        trx_date__lte=company_date
    ).aggregate(total_principal=Sum('principal'))['total_principal'] or 0

    total_interest_between_dates = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle,
        trx_date__gte=disbursement_date,
        trx_date__lte=company_date
    ).aggregate(total_interest=Sum('interest'))['total_interest'] or 0

    last_lp_date = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle,
        trx_type='LP'
    ).aggregate(Max('trx_date'))['trx_date__max']

    if company.session_status == 'Closed':
        return HttpResponse("You cannot post any transaction. Session is closed.")

    if request.method == 'POST':
        form = MemtransForm(request.POST, request.FILES, instance=customer)
        app_date = request.POST.get('app_date')
        if form.is_valid():
            app_date = form.cleaned_data['app_date']
            ses_date = form.cleaned_data['ses_date']

            # Validate that app_date is not greater than ses_date
            if app_date > ses_date:
                messages.error(request, 'Error: The Application Date (app_date) cannot be greater than the Session Date (ses_date).')
                return redirect('loan_repayment', id=id)

            principal = float(request.POST.get('principal'))
            interest = float(request.POST.get('interest'))
            penalty = float(request.POST.get('penalty'))
            total_paid = float(request.POST.get('total_paid'))
            
            with transaction.atomic():
                # Generate a unique transaction ID for this repayment session
                unique_id = generate_loan_repayment_id()
                
                if account.int_to_recev_gl_dr and account.int_to_recev_ac_dr and account.unearned_int_inc_gl and account.unearned_int_inc_ac:
                    debit_transaction = Memtrans(
                        branch=customer.branch,
                        gl_no=form.cleaned_data['gl_no_cashier'],
                        ac_no=form.cleaned_data['ac_no_cashier'],
                        cycle=customer.cycle,
                        amount=-principal,
                        description='Principal Loan Repayment - Debit',
                        type='D',
                        account_type='C',
                        ses_date=company_date,
                        app_date=form.cleaned_data['app_date'],
                        trx_no=unique_id,  # Set trx_no to the unique ID
                        code='LP',
                        user=request.user

                    )
                    debit_transaction.save()

                    credit_transaction = Memtrans(
                        branch=form.cleaned_data['branch'],
                        gl_no=customer.gl_no,
                        ac_no=customer.ac_no,
                        cycle=customer.cycle,
                        amount=principal,
                        description=f'{customers.first_name}, {customers.last_name}, {customers.gl_no}-{customers.ac_no} Principal Loan Repayment - Debit',
                        error='A',
                        type='C',
                        account_type='L',
                        ses_date=form.cleaned_data['ses_date'],
                        app_date=form.cleaned_data['app_date'],
                        trx_no=unique_id,  # Set trx_no to the unique ID
                        code='LP',
                        user=request.user
                    )
                    credit_transaction.save()

                    # Interest transactions
                    debit_transaction_interest = Memtrans(
                        branch=customer.branch,
                        gl_no=form.cleaned_data['gl_no_cashier'],
                        ac_no=form.cleaned_data['ac_no_cashier'],
                        cycle=customer.cycle,
                        amount=-interest,
                        description='Loan Interest - Debit',
                        type='D',
                        account_type='C',
                        ses_date=company_date,
                        app_date=form.cleaned_data['app_date'],
                        trx_no=unique_id,  # Set trx_no to the unique ID
                        code='LP',
                        user=request.user
                    )
                    debit_transaction_interest.save()

                    credit_transaction_interest = Memtrans(
                        branch=form.cleaned_data['branch'],
                        gl_no=account.interest_gl,
                        ac_no=account.interest_ac,
                        cycle=customer.cycle,
                        amount=interest,
                        description=f'{customers.first_name}, {customers.last_name}, {customers.gl_no}-{customers.ac_no}  Interest Repayment - Debit',
                        error='A',
                        type='C',
                        account_type='I',
                        ses_date=form.cleaned_data['ses_date'],
                        app_date=form.cleaned_data['app_date'],
                        trx_no=unique_id,  # Set trx_no to the unique ID
                        code='LP',
                        user=request.user
                    )
                    credit_transaction_interest.save()

                    # Counting existing 'LP' transactions to set the period
                    lp_count = LoanHist.objects.filter(
                        gl_no=customer.gl_no,
                        ac_no=customer.ac_no,
                        cycle=customer.cycle,
                        trx_type='LP'
                    ).count()
                    period = lp_count + 1

                    loanhist_entry = LoanHist(
                        branch=customer.branch,
                        gl_no=customer.gl_no,
                        ac_no=customer.ac_no,
                        cycle=customer.cycle,
                        trx_date=app_date,
                        period=str(period),  # Setting the period based on the count
                        trx_type='LP',
                        trx_naration='Loan Repayment',
                        principal=-principal,
                        interest=-interest,
                        penalty=-penalty,
                        trx_no=unique_id  # Set trx_no to the unique ID
                    )
                    loanhist_entry.save()

                    total_interest = LoanHist.objects.filter(gl_no=customers.gl_no, ac_no=customers.ac_no, cycle=customer.cycle).aggregate(Sum('interest'))['interest__sum'] or 0
                    total_principal = LoanHist.objects.filter(gl_no=customers.gl_no, ac_no=customers.ac_no, cycle=customer.cycle).aggregate(Sum('principal'))['principal__sum'] or 0

                    customer.total_loan = total_principal + total_interest
                    customer.total_interest = total_interest
                    customer.save()

                    # Additional interest transaction for accounting
                    debit_transaction_interest_accounting = Memtrans(
                        branch=customer.branch,
                        gl_no=account.int_to_recev_gl_dr,
                        ac_no=account.int_to_recev_ac_dr,
                        cycle=customer.cycle,
                        amount=-interest,
                        description=f'{customers.first_name}-{customers.last_name}-{customers.gl_no}-{customers.ac_no}',
                        type='D',
                        account_type='I',
                        ses_date=company_date,
                        app_date=form.cleaned_data['app_date'],
                        trx_no=unique_id,  # Set trx_no to the unique ID
                        code='LP',
                        user=request.user
                    )
                    debit_transaction_interest_accounting.save()

                    credit_transaction_interest_accounting = Memtrans(
                        branch=form.cleaned_data['branch'],
                        gl_no=account.unearned_int_inc_gl,
                        ac_no=account.unearned_int_inc_ac,
                        cycle=customer.cycle,
                        amount=interest,
                        description=f'{customers.first_name}-{customers.last_name}-{customers.gl_no}-{customers.ac_no}',
                        type='C',
                        account_type='I',
                        ses_date=company_date,
                        app_date=form.cleaned_data['app_date'],
                        trx_no=unique_id,  # Set trx_no to the unique ID
                        code='LP',
                        user=request.user
                    )
                    credit_transaction_interest_accounting.save()

                    messages.success(request, 'Loan Repayment successfully!')
                    return redirect('choose_loan_repayment')
                else:
                    messages.warning(request, 'Please define all required loan parameters before disbursement.')
                    return redirect('choose_loan_repayment')
    else:
        initial_data = {'gl_no': customer.gl_no}
        form = LoansModifyForm(instance=customer, initial=initial_data)

    return render(request, 'loans/loan_repayment.html', {
        'form': form,
        'customers': customers,
        'customer': customer,
        'cust_data': cust_data,
        'cust_branch': cust_branch,
        'gl_no': gl_no,
        'officer': officer,
        'ac_no_list': ac_no_list,
        'amounts': amounts,
        'account': account,
        'company': company,
        'company_date': company_date,
        'total_principal_currently': total_principal_currently,
        'total_interest_currently': total_interest_currently,
        'total_principal_between_dates': total_principal_between_dates,
        'total_interest_between_dates': total_interest_between_dates,  # Added to context
        'total_principal': total_principal,
        'total_interest': total_interest,
        'last_lp_date': last_lp_date,
    })





@login_required(login_url='login')
@user_passes_test(check_role_admin)
def choose_loan_written_off(request):
    # Filter customers with loan approval status set to 'F'
    customers = Loans.objects.select_related('customer').filter(total_loan__gt=0)
  
    # Pass the customers data to the template
    return render(request, 'loans/choose_loan_written_off.html', {'customers': customers})


#Written-off Loan
@login_required(login_url='login')
@user_passes_test(check_role_admin)  

def loan_written_off(request, id):
    customer = get_object_or_404(Loans, id=id)
    account = get_object_or_404(Account, gl_no=customer.gl_no)
    customers = customer.customer

    cust_data = Account.objects.filter(gl_no__startswith='20').exclude(gl_no__in=['20100', '20200', '20000'])
    gl_no = Account.objects.filter(gl_no__startswith='200').values_list('gl_no', flat=True)
    ac_no_list = Memtrans.objects.filter(ac_no=customer.ac_no).values_list('ac_no', flat=True).distinct()
    cust_branch = Company.objects.all()
    amounts = Memtrans.objects.filter(ac_no=customer.ac_no, gl_no__startswith='2').values('gl_no').annotate(total_amount=Sum('amount')).order_by('-total_amount')
    officer = Account_Officer.objects.all()

    user = User.objects.get(id=request.user.id)
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''
    
    total_principal_currently = LoanHist.objects.filter(trx_date__lt=company_date, gl_no=customer.gl_no,ac_no=customer.ac_no,cycle=customer.cycle).aggregate(Sum('principal'))['principal__sum'] or 0
    total_interest_currently = LoanHist.objects.filter(trx_date__lt=company_date,gl_no=customer.gl_no,ac_no=customer.ac_no, cycle=customer.cycle).aggregate(Sum('interest'))['interest__sum'] or 0

    # Sum the principal using gl_no, ac_no, and cycle
    total_principal = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle
    ).aggregate(Sum('principal'))['principal__sum'] or 0

    # Sum the interest using gl_no, ac_no, and cycle
    total_interest = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle
    ).aggregate(Sum('interest'))['interest__sum'] or 0

    # Calculate the total balance of the loan
    # total_balance = total_principal + total_interest
    # Sum the principal between disbursement and session date
    disbursement_date = customer.disbursement_date
    total_principal_between_dates = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle,
        trx_date__gte=disbursement_date,
        trx_date__lte=company_date
    ).aggregate(total_principal=Sum('principal'))['total_principal'] or 0

    total_interest_between_dates = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle,
        trx_date__gte=disbursement_date,
        trx_date__lte=company_date
    ).aggregate(total_interest=Sum('interest'))['total_interest'] or 0

        # Get the last LP date
    # Calculate the last LP date
    last_lp_date = LoanHist.objects.filter(
        gl_no=customer.gl_no,
        ac_no=customer.ac_no,
        cycle=customer.cycle,
        trx_type='LP'
    ).aggregate(Max('trx_date'))['trx_date__max']

    if company.session_status == 'Closed':
        return HttpResponse("You cannot post any transaction. Session is closed.")

    if request.method == 'POST':
        form = MemtransForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            principal = float(request.POST.get('principal'))
            interest = float(request.POST.get('interest'))
            penalty = float(request.POST.get('penalty'))
            total_paid = float(request.POST.get('total_paid'))
            
            with transaction.atomic():
                # Generate a unique transaction ID for this repayment session
                unique_id = generate_loan_written_off_id()
                
                if account.int_to_recev_gl_dr and account.int_to_recev_ac_dr and account.unearned_int_inc_gl and account.unearned_int_inc_ac:
                    debit_transaction = Memtrans(
                        branch=customer.branch,
                        gl_no=account.writ_off_dr_gl_no,
                        ac_no=account.writ_off_dr_ac_no,
                        cycle=customer.cycle,
                        amount=-principal,
                        description=f'{customers.first_name}, {customers.last_name}, {customers.gl_no}-{customers.ac_no} - Loan Written Off Principal',
                        type='D',
                        account_type='I',
                        ses_date=company_date,
                        trx_no=unique_id  # Set trx_no to the unique ID
                    )
                    debit_transaction.save()

                    credit_transaction = Memtrans(
                        branch=form.cleaned_data['branch'],
                        gl_no=customer.gl_no,
                        ac_no=customer.ac_no,
                        cycle=customer.cycle,
                        amount=principal,
                        description=f'{customers.first_name}, {customers.last_name}, {customers.gl_no}-{customers.ac_no} - Loan Written Off Principal',
                        error='A',
                        type='C',
                        account_type='L',
                        ses_date=form.cleaned_data['ses_date'],
                        trx_no=unique_id  # Set trx_no to the unique ID
                    )
                    credit_transaction.save()


               

                    # Counting existing 'LP' transactions to set the period
                    lp_count = LoanHist.objects.filter(
                        gl_no=customer.gl_no,
                        ac_no=customer.ac_no,
                        cycle=customer.cycle,
                        trx_type='LW'
                    ).count()
                    period = lp_count + 1

                    loanhist_entry = LoanHist(
                        branch=customer.branch,
                        gl_no=customer.gl_no,
                        ac_no=customer.ac_no,
                        cycle=customer.cycle,
                        trx_date=credit_transaction.ses_date,
                        period=str(period),  # Setting the period based on the count
                        trx_type='LW',
                        principal=-principal,
                        interest=-interest,
                        penalty=-penalty,
                        trx_no=unique_id  # Set trx_no to the unique ID
                    )
                    loanhist_entry.save()

                    total_interest = LoanHist.objects.filter(gl_no=customers.gl_no, ac_no=customers.ac_no, cycle=customer.cycle).aggregate(Sum('interest'))['interest__sum'] or 0
                    total_principal = LoanHist.objects.filter(gl_no=customers.gl_no, ac_no=customers.ac_no, cycle=customer.cycle).aggregate(Sum('principal'))['principal__sum'] or 0

                    customer.total_loan = total_principal + total_interest
                    customer.total_interest = total_interest
                    customer.save()

                    # Additional interest transaction for accounting
                    debit_transaction_interest_accounting = Memtrans(
                        branch=customer.branch,
                        gl_no=account.unearned_int_inc_gl,
                        ac_no=account.unearned_int_inc_ac,
                        cycle=customer.cycle,
                        amount=-interest,
                        description=f'{customers.first_name}-{customers.last_name}-{customers.gl_no}-{customers.ac_no} - Loan Written Off interest',
                        type='D',
                        account_type='I',
                        ses_date=company_date,
                        trx_no=unique_id  # Set trx_no to the unique ID
                    )
                    debit_transaction_interest_accounting.save()

                    credit_transaction_interest_accounting = Memtrans(
                        branch=form.cleaned_data['branch'],
                        gl_no=account.int_to_recev_gl_dr,
                        ac_no=account.int_to_recev_ac_dr,
                        cycle=customer.cycle,
                        amount=interest,
                        description=f'{customers.first_name}-{customers.last_name}-{customers.gl_no}-{customers.ac_no} - Loan Written Off interest',
                        type='C',
                        account_type='I',
                        ses_date=company_date,
                        trx_no=unique_id  # Set trx_no to the unique ID
                    )
                    credit_transaction_interest_accounting.save()

                    messages.success(request, 'Loan Repayment successfully!')
                    return redirect('choose_loan_repayment')
                else:
                    messages.warning(request, 'Please define all required loan parameters before disbursement.')
                    return redirect('choose_loan_repayment')
    else:
        initial_data = {'gl_no': customer.gl_no}
        form = LoansModifyForm(instance=customer, initial=initial_data)

    return render(request, 'loans/loan_written_off.html', {
        'form': form,
        'customers': customers,
        'customer': customer,
        'cust_data': cust_data,
        'cust_branch': cust_branch,
        'gl_no': gl_no,
        'officer': officer,
        'ac_no_list': ac_no_list,
        'amounts': amounts,
        'account': account,
        'company': company,
        'company_date': company_date,
        'total_principal_currently': total_principal_currently,
        'total_interest_currently': total_interest_currently,
        'total_principal_between_dates': total_principal_between_dates,
        'total_interest_between_dates':total_interest_between_dates,  # Added to context
        'total_principal':total_principal,
        'total_interest':total_interest,
        'last_lp_date':last_lp_date,
    })





from django.db.models import Sum


@login_required(login_url='login')
@user_passes_test(check_role_admin)
def loan_due(request):
    # Filter customers with approval status 'T'
    customers = Loans.objects.filter(approval_status='T')

    user = User.objects.get(id=request.user.id)
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''

    # Annotate each customer with their total principal and total interest
    for customer in customers:
        customer.total_principal = LoanHist.objects.filter(trx_date__lt=company_date, cycle=customer.cycle).aggregate(total_principal=Sum('principal'))['total_principal'] or 0
        customer.total_interest = LoanHist.objects.filter(trx_date__lt=company_date, cycle=customer.cycle).aggregate(total_interest=Sum('interest'))['total_interest'] or 0

    return render(request, 'loans/loan_due.html', {'customers': customers})







from django.shortcuts import render, redirect, get_object_or_404
from .models import Loans
from django.db.models import F
from transactions.models import Memtrans
from django.contrib import messages

def display_loan_disbursements(request):
    # Query loans that have been disbursed
    disbursement_reversals = Loans.objects.filter(disb_status='T').select_related('customer')

    # Prepare data for rendering in the template
    disbursement_reversals_details = []

    for reversal in disbursement_reversals:
        # Fetch customer details
        customer = reversal.customer
        gl_no = customer.gl_no
        ac_no = customer.ac_no
        cycle = reversal.cycle
        customer_name = f"{customer.first_name} {customer.last_name}"
        
        # Retrieve transaction number and reversal date from Memtrans model
        memtrans_instance = Memtrans.objects.filter(gl_no=gl_no, ac_no=ac_no, cycle=cycle).first()
        trx_no = memtrans_instance.trx_no if memtrans_instance else None
        reversal_date = memtrans_instance.ses_date if memtrans_instance else None
        
        # Append loan details to the list
        disbursement_reversals_details.append({
            'id': reversal.id,
            'customer_name': customer_name,
            'loan_amount': reversal.loan_amount,
            'disbursement_date': reversal.disbursement_date,
            'reversal_date': reversal_date,
            'trx_no': trx_no,
        })

    # Pass data to the template for rendering
    return render(request, 'loans/display_loan_disbursements.html', {'disbursement_reversals': disbursement_reversals_details})




from django.db import transaction
from django.shortcuts import redirect
from django.contrib import messages
from .models import Loans, LoanHist  # Adjust as needed
from transactions.models import Memtrans
from django.utils import timezone
from company.models import Company

def delete_loan_transactions(request, trx_no, id):
    if request.method == 'POST':
        # Ensure CSRF token is validated
        if request.POST.get('csrfmiddlewaretoken'):
            try:
                # Get the company object (assuming there's only one)
                company = Company.objects.first()

                if not company:
                    messages.error(request, 'Company record not found.')
                    return redirect('display_loan_disbursements')

                # Get the current system date
                system_date = timezone.now().date()

                # Check if the company's system date is less than the current system date
                if company.system_date_date >= system_date:
                    with transaction.atomic():
                        # Update Memtrans records with the given trx_no by appending 'H'
                        Memtrans.objects.filter(trx_no=trx_no).update(error='H')
                        
                        # Update Loans record disb_status with 'H'
                        Loans.objects.filter(id=id).update(disb_status='H')
                        
                        # Delete LoanHist records with the given trx_no
                        LoanHist.objects.filter(trx_no=trx_no).delete()

                        # Update Loans record disb_status with 'F'
                        Loans.objects.filter(id=id).update(disb_status='')

                    messages.success(request, f"Transactions with trx_no {trx_no} have been updated and deleted.")
                    return redirect('display_loan_disbursements')
                else:
                    messages.error(request, 'Cannot delete transactions: company system date is less than the current system date.')
                    return redirect('display_loan_disbursements')

            except Exception as e:
                # Handle any exceptions that may occur
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('display_loan_disbursements')
        else:
            messages.error(request, 'Missing CSRF token.')
            return redirect('display_loan_disbursements')
    else:
        messages.error(request, 'Invalid request method.')
        return redirect('display_loan_disbursements')






from transactions.models import Memtrans
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Loans, LoanHist
from customers.models import Customer

def delete_transactions(request, customer_id):
    # Get the customer object
    customer = get_object_or_404(Customer, id=customer_id)

    # Delete transactions associated with the customer's gl_no or ac_no from Memtrans
    Memtrans.objects.filter(gl_no=customer.gl_no).delete()
    Memtrans.objects.filter(ac_no=customer.ac_no).delete()

    messages.success(request, 'Transactions deleted successfully!')
    return redirect('display_customers')






def display_loans(request):
    if request.method == "POST":
        id = request.POST.get('id')
        loan_entry = get_object_or_404(Loans, id=id)
        loan_entry.delete()
        messages.success(request, 'Loan entry deleted successfully!')
        return redirect('display_loans')  # Assuming 'display_loans' is the name of the URL pattern for this view

    loans = Loans.objects.all()
    return render(request, 'loans/display_loans.html', {'loans': loans})



# views.py
from django.shortcuts import render, get_object_or_404
from .models import Loans, LoanHist

def loan_repayment_reversal(request):
    loans = Loans.objects.filter(total_loan__gt=0)
    return render(request, 'loans/loan_repayment_reversal.html', {'loans': loans})

def loan_history(request, loan_id):
    loan = get_object_or_404(Loans, id=loan_id)
    loan_histories = LoanHist.objects.filter(gl_no=loan.gl_no, ac_no=loan.ac_no, cycle=loan.cycle, trx_type='LP')
    return render(request, 'loans/loan_history.html', {'loan': loan, 'loan_histories': loan_histories})


def delete_loan_history(request, loan_hist_id, loan_id):
    loan_hist = get_object_or_404(LoanHist, id=loan_hist_id)
    trx_no = loan_hist.trx_no
    loan_hist.delete()
    Memtrans.objects.filter(trx_no=trx_no).update(error='H')
    return redirect('loan_history', loan_id=loan_id)











# views.py
from datetime import timedelta, date, datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Max
from django.db import transaction
from django.contrib import messages
from .models import Loans, LoanHist
from transactions.models import Memtrans
from company.models import Company
from accounts_admin.models import Account

def calculate_due_date(disbursement_date, payment_freq, num_install):
    if disbursement_date is None:
        return None

    if payment_freq == 'monthly':
        due_date = disbursement_date + timedelta(days=num_install * 30)  # Approximation for monthly
    elif payment_freq == 'weekly':
        due_date = disbursement_date + timedelta(weeks=num_install)
    else:
        due_date = disbursement_date  # Default or unsupported payment frequency
    return due_date

def due_loans(request):
    gl_no = request.GET.get('gl_no', None)
    ac_no = request.GET.get('ac_no', None)
    cycle = request.GET.get('cycle', None)

    company = get_object_or_404(Company, id=request.user.branch_id)
    company_date_str = company.session_date.strftime('%Y-%m-%d') if company.session_date else date.today().strftime('%Y-%m-%d')
    company_date = datetime.strptime(company_date_str, '%Y-%m-%d').date()

    due_loans = Loans.objects.all()
    if gl_no:
        due_loans = due_loans.filter(gl_no=gl_no)
    if ac_no:
        due_loans = due_loans.filter(ac_no=ac_no)
    if cycle:
        due_loans = due_loans.filter(cycle=cycle)

    due_loans = [loan for loan in due_loans if calculate_due_date(loan.disbursement_date, loan.payment_freq, loan.num_install) <= company_date]

    loans_data = []
    for loan in due_loans:
        customer = loan.customer
        disbursement_date = loan.disbursement_date
        total_principal_between_dates = LoanHist.objects.filter(
            gl_no=loan.gl_no,
            ac_no=loan.ac_no,
            cycle=loan.cycle,
            trx_date__gte=disbursement_date,
            trx_date__lte=company_date
        ).aggregate(total_principal=Sum('principal'))['total_principal'] or 0

        total_interest_between_dates = LoanHist.objects.filter(
            gl_no=loan.gl_no,
            ac_no=loan.ac_no,
            cycle=loan.cycle,
            trx_date__gte=disbursement_date,
            trx_date__lte=company_date
        ).aggregate(total_interest=Sum('interest'))['total_interest'] or 0

        last_lp_date = LoanHist.objects.filter(
            gl_no=loan.gl_no,
            ac_no=loan.ac_no,
            cycle=loan.cycle,
            trx_type='LP'
        ).aggregate(Max('trx_date'))['trx_date__max']

        customer_balance = Memtrans.objects.filter(
            gl_no=loan.cust_gl_no,
            ac_no=customer.ac_no,
            error='A'
        ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0

        if total_principal_between_dates > 0:
            loans_data.append({
                'loan': loan,
                'due_date': calculate_due_date(loan.disbursement_date, loan.payment_freq, loan.num_install),
                'total_principal_between_dates': total_principal_between_dates,
                'total_interest_between_dates': total_interest_between_dates,
                'last_lp_date': last_lp_date,
                'loan_amount': loan.loan_amount,
                'cycle': loan.cycle,
                'customer_gl_no': customer.gl_no,
                'customer_phone': customer.phone_no,
                'loan_cust_gl_no': loan.cust_gl_no,
                'customer_ac_no': customer.ac_no,
                'customer_balance': customer_balance  # Add customer balance
            })

    return render(request, 'loans/due_loans.html', {
        'loans_data': loans_data,
        'company_date': company_date,
        'gl_no': gl_no,
        'ac_no': ac_no,
        'cycle': cycle,
    })

def process_repayments(request):
    if request.method == 'POST':
        company = get_object_or_404(Company, id=request.user.branch_id)
        company_date_str = company.session_date.strftime('%Y-%m-%d') if company.session_date else date.today().strftime('%Y-%m-%d')
        company_date = datetime.strptime(company_date_str, '%Y-%m-%d').date()

        loans_data = request.POST.getlist('loans_data')
        for loan_id in loans_data:
            loan = get_object_or_404(Loans, id=loan_id)
            account = get_object_or_404(Account, gl_no=loan.gl_no)
            customer = loan.customer

            principal = LoanHist.objects.filter(
                gl_no=loan.gl_no,
                ac_no=loan.ac_no,
                cycle=loan.cycle,
                trx_date__gte=loan.disbursement_date,
                trx_date__lte=company_date
            ).aggregate(total_principal=Sum('principal'))['total_principal'] or 0

            interest = LoanHist.objects.filter(
                gl_no=loan.gl_no,
                ac_no=loan.ac_no,
                cycle=loan.cycle,
                trx_date__gte=loan.disbursement_date,
                trx_date__lte=company_date
            ).aggregate(total_interest=Sum('interest'))['total_interest'] or 0

            gl_no_cashier = customer.gl_no  # Get gl_no from Customer model where it starts with '2'
            ac_no_cashier = customer.ac_no

            with transaction.atomic():
                unique_id = generate_loan_repayment_id()

                if account.int_to_recev_gl_dr and account.int_to_recev_ac_dr and account.unearned_int_inc_gl and account.unearned_int_inc_ac:
                    debit_transaction = Memtrans(
                        branch=loan.branch,
                        gl_no=loan.cust_gl_no,
                        ac_no=ac_no_cashier,
                        cycle=loan.cycle,
                        amount=-principal,
                        description='Loan Repayment - Debit',
                        type='C',
                        ses_date=company_date,
                        trx_no=unique_id
                    )
                    debit_transaction.save()

                    credit_transaction = Memtrans(
                        branch=loan.branch,
                        gl_no=loan.gl_no,
                        ac_no=loan.ac_no,
                        cycle=loan.cycle,
                        amount=principal,
                        description=f'{customer.first_name}, {customer.last_name}, {customer.gl_no}-{customer.ac_no}',
                        error='A',
                        type='D',
                        ses_date=company_date,
                        trx_no=unique_id
                    )
                    credit_transaction.save()

                    debit_transaction_interest = Memtrans(
                        branch=loan.branch,
                        gl_no=loan.cust_gl_no,
                        ac_no=ac_no_cashier,
                        cycle=loan.cycle,
                        amount=-interest,
                        description='Loan Interest - Debit',
                        type='C',
                        ses_date=company_date,
                        trx_no=unique_id
                    )
                    debit_transaction_interest.save()

                    credit_transaction_interest = Memtrans(
                        branch=loan.branch,
                        gl_no=account.interest_gl,
                        ac_no=account.interest_ac,
                        cycle=loan.cycle,
                        amount=interest,
                        description=f'{customer.first_name}, {customer.last_name}, {loan.gl_no}-{loan.ac_no}',
                        error='A',
                        type='D',
                        ses_date=company_date,
                        trx_no=unique_id
                    )
                    credit_transaction_interest.save()

                    lp_count = LoanHist.objects.filter(
                        gl_no=loan.gl_no,
                        ac_no=loan.ac_no,
                        cycle=loan.cycle,
                        trx_type='LP'
                    ).count()
                    period = lp_count + 1

                    loanhist_entry = LoanHist(
                        branch=loan.branch,
                        gl_no=loan.gl_no,
                        ac_no=loan.ac_no,
                        cycle=loan.cycle,
                        trx_date=credit_transaction.ses_date,
                        period=str(period),
                        trx_type='LP',
                        principal=-principal,
                        interest=-interest,
                        penalty=0,
                        trx_no=unique_id
                    )
                    loanhist_entry.save()

                    loan.total_loan = principal + interest
                    loan.total_interest = interest
                    loan.save()

        messages.success(request, 'All due loans have been processed for repayment.')
        return redirect('due_loans')
    return redirect('due_loans')



@login_required(login_url='login')
@user_passes_test(check_role_admin)
def eop_loans(request):
    return render(request, 'loans/eop_loans.html')






@login_required(login_url='login')
@user_passes_test(check_role_admin)
def choose_to_apply_simple_loan(request):
    data = Memtrans.objects.all().order_by('-id').first()
    customers = Customer.objects.filter(label='L').order_by('-id')
    total_amounts = []
    for customer in customers:
        # Calculate the total amount for each customer
        total_amount = Memtrans.objects.filter(gl_no=customer.gl_no, ac_no=customer.ac_no, error='A').aggregate(total_amount=Sum('amount'))['total_amount']
        total_amounts.append({
            'customer': customer,
            'total_amount': total_amount or 0.0,
        })
    return render(request, 'loans/choose_to_apply_simple_loan.html',{'customers':customers,'total_amounts':total_amounts,'data':data})


# loan application
@login_required(login_url='login')
@user_passes_test(check_role_admin)
def loan_application_and_approval(request, id):
    customer = get_object_or_404(Customer, id=id)
    loan_account = Account.objects.filter(gl_no__startswith='104').exclude(gl_no='10400').exclude(gl_no='104100').exclude(gl_no='104200')
    initial_values = {'gl_no_cust': customer.gl_no, 'ac_no_cust': customer.ac_no}
    user = User.objects.get(id=request.user.id)
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''
    
    
    if company.session_status == 'Closed':
        
        return HttpResponse("You can not post any transaction. Session is closed.") 
    else:
        if request.method == 'POST':
            form = LoansForm(request.POST, request.FILES)
            if form.is_valid():
                gl_no = form.cleaned_data['gl_no']
                ac_no = form.cleaned_data['ac_no']
                
                with transaction.atomic():
                    # Check if there is an existing loan with the same 'gl_no' and 'ac_no'
                    existing_loan = Loans.objects.filter(gl_no=gl_no, ac_no=ac_no).last()

                    if existing_loan:
                        # If an existing loan is found, create a new loan with an incremented cycle
                        new_loan = Loans(
                            branch=form.cleaned_data.get('branch', 0),
                            appli_date=form.cleaned_data.get('appli_date', 0),
                            loan_amount=form.cleaned_data.get('loan_amount', 0),
                            interest_rate=form.cleaned_data.get('interest_rate', 0),
                            payment_freq=form.cleaned_data.get('payment_freq', 0),
                            interest_calculation_method=form.cleaned_data.get('interest_calculation_method', 0),
                            loan_officer=form.cleaned_data.get('loan_officer', 0),
                            business_sector=form.cleaned_data.get('business_sector', 0),
                            customer=customer,
                            gl_no=gl_no,
                            ac_no=ac_no,
                            approval_status='T',
                            approval_date=form.cleaned_data.get('appli_date', 0),
                            
                            num_install=form.cleaned_data.get('num_install', 0),
                            cycle=existing_loan.cycle + 1 if existing_loan.cycle is not None else 1,
                            # ... other fields ...
                        )
                    else:
                        # If no existing loan is found, create a new loan with cycle 1
                        new_loan = Loans(
                            branch=form.cleaned_data.get('branch', 0),
                            appli_date=form.cleaned_data.get('appli_date', 0),
                            loan_amount=form.cleaned_data.get('loan_amount', 0),
                            interest_rate=form.cleaned_data.get('interest_rate', 0),
                            payment_freq=form.cleaned_data.get('payment_freq', 0),
                            interest_calculation_method=form.cleaned_data.get('interest_calculation_method', 0),
                            loan_officer=form.cleaned_data.get('loan_officer', 0),
                            business_sector=form.cleaned_data.get('business_sector', 0),
                            customer=customer,
                            gl_no=gl_no,
                            ac_no=ac_no,
                            approval_status='T',
                            approval_date=form.cleaned_data.get('appli_date', 0),
                            
                            num_install=form.cleaned_data.get('num_install', 0),
                            cycle=1,
                            # ... other fields ...
                        )

                    new_loan.save()
                    customer.loan = 'T'
                    customer.save()
                    print("Customer:", customer)  # Print the customer object for debugging

                    messages.success(request, 'Loan Applied successfully!')
                    return redirect('choose_to_apply_simple_loan')
            
            else:
                messages.error(request, 'Form is not valid. Please check the entered data.')
        else:
            form = LoansForm(initial=initial_values)

    return render(request, 'loans/loan_application_and_approval.html', {'form': form, 'customer': customer, 'loan_account': loan_account,'company':company, 'company_date':company_date})





@login_required(login_url='login')
@user_passes_test(check_role_admin)
def choose_simple_disburse(request):
    customers = Loans.objects.select_related('customer').filter(approval_status='T',disb_status='F')
    for customer in customers:
        if customer.customer:
            print(customer.customer.first_name)
        else:
            print("No associated customer for this loan.")
    # Pass the customers data to the template
    return render(request, 'loans/choose_simple_disburse.html', {'customers': customers})




def simple_loan_disbursement(request, id):
    loan = get_object_or_404(Loans, id=id)
    account = get_object_or_404(Account, gl_no=loan.gl_no)
    customer = loan.customer  # Assuming loan.customer is a ForeignKey to Customer model
    
    cust_data = Account.objects.filter(gl_no__startswith='20').exclude(gl_no__in=['20100', '20200', '20000'])
    gl_no = Account.objects.filter(gl_no__startswith='200').values_list('gl_no', flat=True)
    ac_no_list = Memtrans.objects.filter(ac_no=loan.ac_no).values_list('ac_no', flat=True).distinct()
    cust_branch = Company.objects.all()
    amounts = Memtrans.objects.filter(ac_no=loan.ac_no, gl_no__startswith='2').values('gl_no').annotate(total_amount=Sum('amount')).order_by('-total_amount')
    officer = Account_Officer.objects.all()
    
    user = request.user
    branch_id = user.branch_id
    company = get_object_or_404(Company, id=branch_id)
    company_date = company.session_date.strftime('%Y-%m-%d') if company.session_date else ''
    
    if loan.appli_date:
        appli_date = loan.appli_date.strftime('%Y-%m-%d')
    else:
        appli_date = ''
    
    if loan.approval_date:
        approve_date = loan.approval_date.strftime('%Y-%m-%d')
    else:
        approve_date = ''
    
    if company.session_status == 'Closed':
        return HttpResponse("You cannot post any transaction. Session is closed.")
    else:
        if request.method == 'POST':
            form = MemtransForm(request.POST, request.FILES)
            if form.is_valid():
                ses_date = form.cleaned_data['ses_date']
                if ses_date > company.session_date:
                    messages.warning(request, 'Transaction date cannot be greater than the session date.')
                    return redirect('choose_to_disburse')
                
                customer_id = customer.id  # Assuming the customer ID is in the form data
                with transaction.atomic():
                    if account.int_to_recev_gl_dr and account.int_to_recev_ac_dr and account.unearned_int_inc_gl and account.unearned_int_inc_ac:
                        # Generate a unique transaction number
                        unique_trx_no = generate_loan_disbursement_id()

                        debit_transaction = Memtrans(
                            branch=loan.branch,
                            customer_id=customer_id,  # Use the customer ID from the form data
                            cycle=loan.cycle,
                            gl_no=loan.gl_no,
                            ac_no=loan.ac_no,
                            amount=-loan.loan_amount,
                            description='Loan Disbursement - Debit',
                            type='D',
                            ses_date=company_date,
                            trx_no=unique_trx_no
                        )
                        debit_transaction.save()

                        credit_transaction = Memtrans(
                            branch=form.cleaned_data['branch'],
                            customer_id=customer_id,  # Use the customer ID from the form data
                            cycle=loan.cycle,
                            gl_no=form.cleaned_data['gl_no_cashier'],
                            ac_no=form.cleaned_data['ac_no_cashier'],
                            amount=loan.loan_amount,
                            description=f'{customer.first_name}, {customer.last_name}, {customer.gl_no}-{customer.ac_no}',
                            error='A',
                            type='C',
                            ses_date=form.cleaned_data['ses_date'],
                            trx_no=unique_trx_no
                        )
                        credit_transaction.save()

                        # Calculate loan schedule
                        loan_schedule = loan.calculate_loan_schedule()
                        loan.disb_status = 'T'
                        loan.cust_gl_no = form.cleaned_data['gl_no_cashier']
                        loan.disbursement_date = form.cleaned_data['ses_date']
                        loan.save()

                        # Insert loan schedule into LoanHist
                        for payment in loan_schedule:
                            loanhist_entry = LoanHist(
                                branch=loan.branch,
                                gl_no=loan.gl_no,
                                ac_no=loan.ac_no,
                                cycle=loan.cycle,
                                period=payment['period'],
                                trx_date=payment['payment_date'],
                                trx_type='LD',
                                principal=payment['principal_payment'],
                                interest=payment['interest_payment'],
                                penalty=0,
                                trx_no=unique_trx_no
                            )
                            loanhist_entry.save()

                        # Sum the interest from LoanHist
                        total_interest = LoanHist.objects.filter(gl_no=loan.gl_no, ac_no=loan.ac_no, cycle=loan.cycle).aggregate(total_interest=Sum('interest'))['total_interest'] or 0

                        # Update loan balance in Loans model
                        loan.total_loan = loan.loan_amount + total_interest
                        loan.total_interest = total_interest
                        loan.save()

                        debit_transaction = Memtrans(
                            branch=loan.branch,
                            customer_id=customer_id,
                            gl_no=account.int_to_recev_gl_dr,
                            ac_no=account.int_to_recev_ac_dr,
                            amount=-loan.total_interest,
                            description=f'{customer.first_name}, {customer.last_name}, {customer.gl_no}-{customer.ac_no}, Disbursement',
                            type='L',
                            ses_date=timezone.now(),
                            trx_no=unique_trx_no
                        )
                        debit_transaction.save()

                        credit_transaction = Memtrans(
                            branch=form.cleaned_data['branch'],
                            customer_id=customer_id,
                            gl_no=account.unearned_int_inc_gl,
                            ac_no=account.unearned_int_inc_ac,
                            amount=loan.total_interest,
                            description=f'{customer.first_name}, {customer.last_name}, {customer.gl_no}-{customer.ac_no}, Interest on Loan - Credit',
                            type='L',
                            ses_date=timezone.now(),
                            trx_no=unique_trx_no
                        )
                        credit_transaction.save()

                        messages.success(request, 'Loan Disbursed successfully!')
                        return redirect('choose_to_disburse')
                    else:
                        messages.warning(request, 'Please define all required loan parameters before disbursement.')
                        return redirect('choose_to_disburse')
        else:
            initial_data = {'gl_no': loan.gl_no}
            form = LoansModifyForm(instance=loan, initial=initial_data)

    return render(request, 'loans/simple_loan_disbursement.html', {
        'form': form,
        'customers': customer,
        'loan': loan,
        'customer': loan,
        'cust_data': cust_data,
        'cust_branch': cust_branch,
        'gl_no': gl_no,
        'officer': officer,
        'ac_no_list': ac_no_list,
        'amounts': amounts,
        'account': account,
        'company': company,
        'company_date': company_date,
        'appli_date':appli_date,
        'approve_date':approve_date,
    })






