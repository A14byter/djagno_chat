from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    def __str__(self):

        return self.phone_number
        
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=40, blank=True,null=True)
    phone_number=models.CharField(max_length=11)
    profile_picture=models.ImageField(blank=True, null=True)
    bio=models.TextField(max_length=400,blank=True,null=True)

