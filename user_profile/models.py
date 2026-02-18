from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, default='partner')
    cycle_length = models.IntegerField(default=28)
    period_duration = models.IntegerField(default=5)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    partners = models.ManyToManyField('self', blank=True, symmetrical=False)
    sex = models.CharField(
        max_length=10, 
        choices=[
            ('none', 'None'),
            ('male', 'Male'), 
            ('female', 'Female')
        ],
        null=True,
        blank=False
    )

    def __str__(self):
        return f"Profile of {self.user.username}"
