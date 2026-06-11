
from django.contrib import admin
from django.urls import path
from chat.views import chat, chatlist, addchat,user_profile_view
from app.views import signup,loginview,code_login,code_check

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chatlist/',chatlist, name='chatlist'),
    path('chat/<slug:slug>/',chat,name='chat'),

    path('signup/',signup,name='signup'),
    path('login/',loginview,name='login'),
    path('code-login/',code_login,name='code_login'),
    path('code-check' , code_check,name='code_check'),

    path('add-chat/',addchat,name='add_chat'),
    path('user-profile/<slug:chat_slug>',user_profile_view ,name='user_profile')

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
