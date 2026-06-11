from django.shortcuts import render,redirect

from chat.models import Chat

from django.contrib.auth.models import User
from djangochat import settings
from .models import Account
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.auth.decorators import login_required

import string
import secrets
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import re

def signup(request):
    context=None
    error=None
    if request.method == 'POST':
        phone_number=request.POST.get('phone_number')
        name =request.POST.get('name')
        last_name = request.POST.get('last_name')
        username= request.POST.get('username')
        email=request.POST.get('email')
        
        password=request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')


        request.session['phone_number'] = phone_number
        request.session['name']= name
        request.session['last_name'] = last_name
        request.session['username']=username
        request.session['email']= email
        request.session['password'] = password
        request.session['confirm_password']= confirm_password


       

        
        try:
            int(phone_number)
            valid=True
        except ValueError:
            valid=False

        pattern=  r'^[a-zA-Z]+$'


        name_check=bool(re.match(pattern,name))
        last_name_check=bool(re.match(pattern,last_name))

        if Account.objects.filter(phone_number=phone_number).exists():
            error='user alredy exist. login .'


        elif name_check is False or last_name_check is False :
            error='not a real name. xd'
            del request.session['name']
            del request.session['last_name']
        
        elif User.objects.filter(email=email).exists():
            error= 'this email is being used.'
            del request.session['email']

        elif User.objects.filter(username=username).exists():
            error='this username is being used ,please choose anaoter user name.'
            del request.session['username']

        
        elif phone_number!='' and valid is False:
            error='enter an valid phone number'
            del request.session['phone_number']

        elif email !=None and not ('@' or '.com') in email:
            error ='enter a valid email' 
            del request.session['email']

        elif password !=confirm_password:
            error='passwords are not same.'
            del request.session['confirm_password']

        elif len(password)<8:
            error='password must be at least 8 characters.'
            del request.session['password']
            del request.session['confirm_password']    
        else:
            user=User.objects.create_user(
                
                email=email,
                username=username,
                password=password
            )
            Account.objects.create(name= name , last_name = last_name,user=user, phone_number=phone_number)
            login(request,user)

            del request.session['phone_number']
            del request.session['name']
            del request.session['last_name']
            del request.session['username']
            del request.session['email']
            del request.session['password']
            del request.session['confirm_password']

            return redirect('chatlist')

    context = {
            'phone_number':request.session.get('phone_number',''),
            'name':request.session.get('name',''),
            'last_name':request.session.get('last_name',''),
            'username':request.session.get('username',''),
            'email':request.session.get('email',''),
            'password':request.session.get('password',''),
            'confirm_password':request.session.get('confirm_password','')
        }
            
   

    return render(request,'app/signup.html',{'error':error,'context':context})

        

def loginview(request):
    error=None
    if request.method == 'POST':
        phone_number=request.POST.get('phone_number')
        password=request.POST.get('password')
        account=Account.objects.filter(phone_number=phone_number).first()
        
        
        if not account:
            error = 'account does not exists.'

        elif not check_password(password,account.user.password) :
            error = 'password is wrong you can log in via email.'
        else:
            user=account.user
            login(request,user)
            return redirect('chatlist')

    return render(request,'app/login.html',{'error':error})
    
        
def code_login(request):
    error = None
    expiry_age = None
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            account = Account.objects.filter(user=user).first()
            
            # بررسی وجود کد فعال و غیرمنقضی
            if 'code' in request.session:
                expiry_age = request.session.get_expiry_age()
                if expiry_age > 0:
                    error = 'please wait for another request.'
                else:
                    
                    del request.session['code']
                    del request.session['email']
                    expiry_age = None   
            
            if not error:
                characters = string.ascii_letters + string.digits
                code = ''.join(secrets.choice(characters) for _ in range(6))
                request.session['email'] = email
                request.session['code'] = code
                request.session.set_expiry(180)  

                # ارسال ایمیل
                subject = 'ChatGram code'
                from_email = settings.DEFAULT_FROM_EMAIL
                html_content = render_to_string('app/emails.html', {
                    'name': account.name if account else user.username,
                    'code': code
                })
                msg = EmailMultiAlternatives(subject, '', from_email, [user.email])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

                return redirect('code_check')
        else:
            error = 'user not found'

    return render(request, 'app/code_login.html', {
        'error': error,
        'expiry_age': expiry_age,
    })    


def code_check(request):
    error=None
    if request.method == 'POST':

        code=request.POST.get('code')

        if code == request.session.get('code',0):
            user=User.objects.filter(email=request.session.get('email','')).first()

            if user:
                del request.session['code']
                del request.session['email']
                login(request,user)
                return redirect('chatlist')
            else:
                error='user not found'
        else:
            error='wrong code,you can wait 3 min and request code again.'
            
    return render(request,'app/code_check.html',{'error':error})
        

    

