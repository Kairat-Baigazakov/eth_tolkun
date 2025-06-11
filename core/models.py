# core/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Суперадмин'),
        ('moderator', 'Модератор'),
        ('user', 'Пользователь'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')


class RoomLayout(models.Model):
    name = models.CharField("Наименование номера", max_length=100)
    capacity = models.PositiveIntegerField("Количество мест")
    floor = models.PositiveIntegerField("Этаж")
    building_type = models.CharField("Тип корпуса", max_length=100)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.capacity} мест, этаж {self.floor})"


class Rate(models.Model):
    name = models.CharField("Наименование", max_length=100)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    vat = models.DecimalField("НДС (%)", max_digits=5, decimal_places=2, help_text="Процент НДС, например 20.00")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    building_type = models.CharField("Тип корпуса", max_length=100, blank=True, null=True)
    room_layout = models.ForeignKey(
        RoomLayout,
        verbose_name="Планировка номера",
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.name} — {self.price} сом. (+{self.vat}% НДС)"


class Arrival(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активный'),
        ('inactive', 'Неактивный'),
    ]

    name = models.CharField(max_length=200, verbose_name="Наименование заезда")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Статус")
    start_date = models.DateField(verbose_name="Дата начала заезда")
    end_date = models.DateField(verbose_name="Дата окончания заезда")
    application_start = models.DateTimeField(verbose_name="Дата и время начала подачи заявки")
    application_end = models.DateTimeField(verbose_name="Дата и время окончания подачи заявки")
    rate = models.ForeignKey('Rate', on_delete=models.PROTECT, verbose_name="Тариф для заезда")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
