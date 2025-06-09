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

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    tab_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.tab_number})"

class Relative(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    relation = models.CharField(max_length=50)
    birth_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.relation})"

class Building(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class RoomType(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.capacity} мест)"

class Room(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    number = models.CharField(max_length=10)

    def __str__(self):
        return f"№{self.number} — {self.room_type} / {self.building}"

class Arrival(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    apply_start = models.DateTimeField()
    apply_end = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} – {self.end_date})"

class Price(models.Model):
    arrival = models.ForeignKey(Arrival, on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.arrival}: {self.room_type} / {self.building}"

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE)
    arrival = models.ForeignKey('Arrival', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.arrival} ({self.status})"
