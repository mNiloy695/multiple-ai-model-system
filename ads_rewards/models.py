from django.db import models
from django.contrib.auth import get_user_model
User=get_user_model()
# Create your models here.


class RewardsHistory(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='rewards',blank=True)
    reward=models.IntegerField()
    # reward_=models.IntegerField(default=1)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.reward}'
