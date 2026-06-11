from django.shortcuts import render , redirect

from django.contrib.auth.models import User
from .models import Chat , Message
from app.models import Account
from django.contrib.auth.decorators import login_required


from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse


@login_required(login_url='login')
def addchat(request):
    error=None
    user=request.user
    account=Account.objects.filter(user=user).first()
    if not account:
        error='something went wrong.you still have no a profile please make one'
        return render(request, 'chat/addchat.html', {'error': error})

    if request.method == 'POST':
        phone_number=request.POST.get('phone_number')
        username=request.POST.get('username')
        

        if phone_number:
            target_account=Account.objects.filter(phone_number=phone_number).first()
            

            
                
            if target_account:
                target_user=target_account.user

                exists_chat=Chat.objects.filter(users=user).filter(users=target_user).distinct().first()

                if exists_chat:
                    error='you already have a private chat with this user.'
                    
                else:
                    if user!=target_user:

                        chat = Chat.objects.create(
                                                    name=f'{account.name}_{target_account.name}',
                                                    slug=f'{user.username}_{target_user.username}')
                        chat.users.add(user,target_user)
                        return redirect('chat',chat.slug)
                    else:
                        chat = Chat.objects.create(
                            name='saved messages',
                            slug=f'{user.username}'
                        )
                        chat.users.add(user)
                        return redirect('chat',chat.slug)
            else:
                error='no such user with this phone number exists.'

        elif username :

            target_user=User.objects.filter(username=username).first()

            if target_user:
                target_account=Account.objects.filter(user=target_user).first()

                exists_chat=Chat.objects.filter(users=user).filter(users=target_user).distinct().first()
                if exists_chat:

                    error='you already have a private chat with this use. '
                else:
                    if user!=target_user:
                        chat=Chat.objects.create(
                                                name=f'{account.name}_{target_account.name}',
                                                slug=f'{user.username}_{target_user.username}')
                        chat.users.add(user,target_user)
                        return redirect('chat',chat.slug)
                    else:
                        chat=Chat.objects.create(
                            name='saved messages',
                            slug=f'{user.username}'

                        )
                        chat.users.add(user)
                        return redirect('chat',chat.slug)
            else:
                error = 'no such user exists.'
        else:
            error='please input a valid data'

    return render(request,'chat/addchat.html',{'error':error})

@login_required(login_url='login')
def chatlist(request):
    error=None
    user=request.user
    chats=Chat.objects.filter(users=user)
    if not chats:
        error='No Chat here yet,start some!'

    return render(request,'chat/chatlist.html',{'chats':chats,'error':error})


@login_required(login_url='login')
def chat(request,slug):
    error=None
    contact_user=None
    user=request.user
    chat=Chat.objects.filter(slug=slug,users=user).first()
    if not chat:
        error='no chat exists.'
        return render(request,'chats/error.html',{'error':error})

    chat_users=chat.users
    for chat_user in chat_users.all():
        if chat_user!=user:
            contact_user = chat_user
            break

    messages=Message.objects.filter(chat=chat).order_by('time')
    if request.method == 'POST':
        text = request.POST.get('text', '')
        photo = request.FILES.get('photo')
        file = request.FILES.get('file')
        # 1. گرفتن شناسه پیام مادر از فرانت‌آند (باید در FormData فرستاده شود)
        target_message_id = request.POST.get('target_message_id') 

        if not text and not photo and not file:
            error = 'choose something to send.'
        else:
            # 2. پیدا کردن پیام مادر در دیتابیس
            reply_to_msg = None
            if target_message_id:
                reply_to_msg = Message.objects.filter(chat=chat, id=target_message_id).first()

            # 3. ذخیره پیام جدید همراه با فیلد reply_to
            msg = Message.objects.create(
                user=user, 
                chat=chat, 
                text=text, 
                photo=photo, 
                file=file,
                reply_to=reply_to_msg # 👈 اضافه شدن رابطه ریپلای
            )
            
            photo_url = request.build_absolute_uri(msg.photo.url) if msg.photo else None
            file_url = request.build_absolute_uri(msg.file.url) if msg.file else None

            channel_layer = get_channel_layer()
            
            # 4. اگر پیام ریپلای بود، نوع رسانه را فرستاده و به سیگنال متفاوتی هدایتش می‌کنیم
            if reply_to_msg:
                async_to_sync(channel_layer.group_send)(
                    f"chat_{chat.slug}",
                    {
                        "type": "reply", # 👈 هدایت به متد reply کانزومر برای هماهنگی فرانت‌آند
                        "room": chat.slug,
                        "user": user.username,
                        "target_message_id": reply_to_msg.id,
                        "reply_to_user": reply_to_msg.user.username,
                        "reply_to_text": reply_to_msg.text[:30] if reply_to_msg.text else "file",
                        "the_message":msg.text,
                        "photo":photo_url,
                        "file":file_url,
                        'message_id':msg.id
                    }
                )
            else:
                # ارسال عادی چت (اگر ریپلای نبود)
                async_to_sync(channel_layer.group_send)(
                    f"chat_{chat.slug}",
                    {
                        "type": "chat_message",
                        "message": msg.text,
                        "message_id": msg.id,
                        "username": user.username,
                        "photo": photo_url,
                        "file": file_url,
                        "room": chat.slug
                    }
                )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
            'success': True
        })

        

    return render(request,'chat/chat.html',{'chat':chat,'user':user,'messages':messages,'contact_user':contact_user,'error':error})


def user_profile_view(request,chat_slug):
    user=request.user
    chat=Chat.objects.filter(slug=chat_slug,users=user).first()
    if not chat:
        error='no such chat exisra'
    else:
        for u in chat.users.all():
            if not u == user:
                target_user = u 
            break
    target_account= Account.objects.filter(user=target_user).first()

    return render(request,'chat/userprofile.html',{'tarhet_account':target_account})
    

