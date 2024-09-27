from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db.models.fields.related import ForeignKey, OneToOneField
from accounts_admin.models import Account

from company.models import Company




class Role(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
    
# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, role, branch, phone_number, cashier_gl,cashier_ac, password=None):
        if not email:
            raise ValueError('User must have an email address')

        if not username:
            raise ValueError('User must have an username')

        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
            role = role,
            branch = branch,
            phone_number = phone_number,
            cashier_gl = cashier_gl,
            cashier_ac = cashier_ac,
            
          
            
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, username, email, password=None):
        user = self.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            role=User.SYSTEM_ADMINISTRATOR,
            branch=Company.objects.get(id=1),  # Set a default branch (replace with the correct Company instance)
            phone_number='N/A',
            cashier_gl=None,
            cashier_ac=None,
            password=password,
        )
        user.is_admin = True
        user.is_active = True  # You may want to set the superuser as active
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    SYSTEM_ADMINISTRATOR = 1
    GENERAL_MANAGER = 2
    BRANCH_MANAGER = 3
    ASSISTANT_MANAGER = 4
    ACCOUNTANT = 5
    ACCOUNTS_ASSISTANT = 6
    CREDIT_SUPERVISOR = 7
    CREDIT_OFFICER = 8
    VERIFICATION_OFFICER = 9
    CUSTOMER_SERVICE_UNIT = 10
    TELLER = 11
    M_I_S_OFFICER = 12


    MALE = 1
    FEMALE = 2

    ROLE_CHOICE = (
        (SYSTEM_ADMINISTRATOR, 'System Administration'),
        (GENERAL_MANAGER, 'Genaral Manager'),
        (BRANCH_MANAGER, 'Branch Manager'),
        (ASSISTANT_MANAGER, 'Assistant Manager'),
        (ACCOUNTANT, 'Accountant'),
        (ACCOUNTS_ASSISTANT, 'Account Assistant'),
        (CREDIT_SUPERVISOR, 'Credit Supervisor'),
        (CREDIT_OFFICER, 'Credit Officer'),
        (VERIFICATION_OFFICER, 'Verification Officer'),
        (CUSTOMER_SERVICE_UNIT, 'Customer Service Unit'),
        (TELLER, 'Teller'),
        (M_I_S_OFFICER, 'Management Information System'),
    )

    profile_picture = models.ImageField(upload_to='users/profile_pictures', default='images/avatar.jpg')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=12, blank=True, null=True)
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICE, blank=True, null=True)
    branch = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, default=None)
    cashier_gl = models.CharField(max_length=6, blank=True, null=True)
    cashier_ac = models.CharField(max_length=1, blank=True, null=True)
    # role = models.ForeignKey(Role, on_delete=models.CASCADE, default='1')

    # required fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def get_role(self):
        if self.role == 1:
            user_role = 'System Administration'
        elif self.role == 2:
            user_role = 'Genaral Manager'
        elif self.role == 3:
            user_role = 'Branch Manager'
        elif self.role == 4:
            user_role = 'Assistant Manager'
        elif self.role == 5:
            user_role = 'Accountant'
        elif self.role == 6:
            user_role = 'Account Assistant'
        elif self.role == 7:
            user_role = 'Credit Supervisor'
        elif self.role == 8:
            user_role = 'Credit Officer'
        elif self.role == 9:
            user_role = 'Verification Officer'
        elif self.role == 10:
            user_role = 'Customer Service Unit'
        elif self.role == 11:
            user_role = 'Teller'
        elif self.role == 12:
            user_role = 'Management Information System'
        return user_role




class UserProfile(models.Model):
    user = OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    # profile_picture = models.ImageField(upload_to='users/profile_pictures', blank=True, null=True)
    
    
    address = models.CharField(max_length=250, blank=True, null=True)
    country = models.CharField(max_length=15, blank=True, null=True)
    state = models.CharField(max_length=15, blank=True, null=True)
    city = models.CharField(max_length=15, blank=True, null=True)
   
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # def full_address(self):
    #     return f'{self.address_line_1}, {self.address_line_2}'

    def __str__(self):
        return self.user.email
    




class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    function_used = models.CharField(max_length=255)
    date_time = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField()

    def __str__(self):
        return f"{self.user.username} - {self.function_used} at {self.date_time}"
    





class Clents(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField()

    def __str__(self):
        return self.name
