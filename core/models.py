# core/models.py
import json
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Суперадмин'),
        ('moderator', 'Модератор'),
        ('user', 'Пользователь'),
    ]

    patronymic = models.CharField('Отчество', max_length=100, blank=True)
    birthdate = models.DateField('Дата рождения', null=True, blank=True)
    position = models.CharField('Должность', max_length=100, blank=True)
    relatives = models.ManyToManyField('Relative', blank=True, related_name='users')
    quota = models.PositiveIntegerField('Количество квот', default=3)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    @property
    def total_quota(self):
        return self.quota + self.relative_set.filter(is_employee_child=True).count()

    def get_active_applications(self, exclude_application=None):
        active_statuses = ['new', 'sent', 'approved', 'revision']
        qs = self.applications.filter(status__in=active_statuses)
        if exclude_application:
            qs = qs.exclude(id=exclude_application.id)
        return qs

    def get_used_quota(self, exclude_application=None):
        used = 0
        for app in self.get_active_applications(exclude_application=exclude_application):
            try:
                guests = json.loads(app.guests or '[]')
                used += sum(1 for g in guests if g.get('quota_type') == 'Льготная квота')
            except Exception:
                pass
        return used

    def get_free_quota(self, exclude_application=None):
        return self.total_quota - self.get_used_quota(exclude_application=exclude_application)



class Relative(models.Model):
    last_name = models.CharField('Фамилия', max_length=100)
    first_name = models.CharField('Имя', max_length=100)
    patronymic = models.CharField('Отчество', max_length=100, blank=True)
    birthdate = models.DateField('Дата рождения')
    relation = models.CharField('Родственные отношения', max_length=50)  # Можно сделать choices
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='relative_set')
    is_employee_child = models.BooleanField('Является ребенком сотрудника', default=False)
    # любые доп. поля

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic} ({self.relation})"


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


class Application(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('sent', 'Отправлена'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
        ('cancelled', 'Отменена'),
        ('revision', 'На доработке'),
    ]
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Не оплачена'),
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачена'),
    ]

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания заявки")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор заявки", related_name='applications')
    arrival = models.ForeignKey('Arrival', on_delete=models.CASCADE, verbose_name="Связанный заезд", related_name='applications')
    guests = models.TextField(verbose_name="Список отдыхающих")
    rooms = models.TextField(verbose_name="Комнаты отдыхающих", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус заявки")
    comment = models.TextField('Комментарий', blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='unpaid', verbose_name="Статус оплаты")
    document = models.FileField(upload_to='applications/docs/', blank=True, null=True, verbose_name="Прикрепленный документ")
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата и время отправки заявки")

    def __str__(self):
        return f"Заявка №{self.id} ({self.author.username})"


class RoomLayout(models.Model):
    name = models.CharField("Наименование номера", max_length=100)
    capacity = models.PositiveIntegerField("Количество мест")
    floor = models.PositiveIntegerField("Этаж")
    building_type = models.CharField("Тип корпуса", max_length=100)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.capacity} мест, этаж {self.floor})"


class RoomPlacement(models.Model):
    arrival = models.ForeignKey(Arrival, on_delete=models.CASCADE, related_name='room_placements')
    room = models.ForeignKey(RoomLayout, on_delete=models.CASCADE, related_name='placements')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='placements')
    guest_fio = models.CharField("ФИО гостя", max_length=200)  # или связь с отдельной моделью Guest, если появится
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.guest_fio} -> {self.room.name} ({self.arrival.name})"


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