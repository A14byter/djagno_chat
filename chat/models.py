from django.db import models
from django.contrib.auth.models import User
class Chat(models.Model):
    def __str__(self):
        return self.name
        
    users=models.ManyToManyField(User)

    name=models.CharField(max_length=50)
    slug=models.SlugField()

class Message(models.Model):
    def __str__(self):
        return self.user.username
    
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    chat=models.ForeignKey(Chat,on_delete=models.CASCADE )

    text=models.TextField(max_length=10000 ,blank=True,null=True)
    photo=models.ImageField( blank= True ,null= True)
    file=models.FileField(blank=True,null=True)

    read=models.BooleanField(default=False)
    time=models.DateTimeField(auto_now_add=True)
    

    reply_to=models.ForeignKey('self',on_delete=models.SET_NULL,blank=True,null=True)

    



