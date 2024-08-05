from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Collection(models.Model):
    user = models.ForeignKey(User,blank=True,null=True,on_delete=models.CASCADE)
    name = models.CharField(blank=True,null=True,max_length=64)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.name)
    
class Item(models.Model):
    collection = models.ForeignKey(Collection,null=True,on_delete=models.CASCADE)
    name = models.CharField(blank=False,null=True,max_length=64)
    created = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='images',blank=True,null=True)

    def __str__(self) -> str:
        return str(self.name)
    