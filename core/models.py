# core/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Суперадмин'),
        ('moderator', 'Модератор'),
        ('user', 'Пользователь'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')