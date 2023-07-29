from django.shortcuts import render

'''
List of Views:
- REGISTER PAGE: To register a new user.
- LOGIN PAGE: To login a registered user.
- LOGOUT PAGE: To logout a registered user.
- ACOOUNT SETTINGS PAGE : To update profile pic and full name.
- VERDICT PAGE: Shows the verdict to the submission.
- SUBMISSIONS PAGE: To view all the submissions made by current logged-in user.
- LEADERBOARD: Diplay the leaderboard.
'''

from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_protect
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes,force_str

#from .tokens import account_activation_token
from USERS.models import User, Submission
from OJ.models import Problem, TestCase
from .forms import CreateUserForm
from datetime import datetime
from time import time

import os
import sys
import subprocess
from subprocess import PIPE
import os.path
#import docker


###############################################################################################################################


# To register a new user
def registerPage(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data.get('email')
            if User.objects.filter(email=user_email).exists():
                messages.error(request,'Email already exist!')
                context = {'form': form}
                return render(request, 'USERS/register.html', context)

            user = form.save(commit=False)
            user.is_active = False
            user.save()
            messages.success(request, 'Account created successfully! ')

            username = form.cleaned_data.get('username')
            current_site = get_current_site(request)

            return redirect('login')

    else:
        form = CreateUserForm()
    context = {'form': form}
    return render(request, 'USERS/register.html', context)

 

###############################################################################################################################


# To login a registered user
def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request, 'Username/Password is incorrect')

        context = {}
        return render(request, 'USERS/login.html', context)


  

###############################################################################################################################


# To logout a registered user
def logoutPage(request):
    logout(request)
    return redirect('login')





###############################################################################################################################


# To view all the submissions made by current logged-in user
@login_required(login_url='login')
def allSubmissionPage(request):
    submissions = Submission.objects.filter(user=request.user.id)
    return render(request, 'USERS/submission.html', {'submissions': submissions})
