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
        ('check_pay', 'Проверьте оплату'),
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
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата и время отправки заявки")
    guests_placemented = models.BooleanField(default=False, verbose_name="Все гости размещены")

    def __str__(self):
        return f"Заявка №{self.id} ({self.author.username})"

    def check_guests_placemented(self):
        """
        Проверяет, размещены ли все гости заявки.
        """
        try:
            guests = json.loads(self.guests or '[]')
        except Exception:
            guests = []
        guests_fio = set(
            " ".join([g.get("last_name", ""), g.get("first_name", ""), g.get("patronymic", "")]).strip().lower()
            for g in guests if g.get("last_name") or g.get("first_name")
        )
        # Все fio из связанных RoomPlacement
        placements = set(
            (fio or '').strip().lower()
            for fio in self.placements.values_list('guest_fio', flat=True)
        )
        all_placed = guests_fio <= placements

        # Обновляем поле только если изменилось
        if self.guests_placemented != all_placed:
            self.guests_placemented = all_placed
            self.save(update_fields=['guests_placemented'])
        return all_placed


class ApplicationDocument(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='applications/docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Документ для заявки #{self.application.id}"


class RoomLayout(models.Model):
    BUILDING_TYPE_CHOICES = [
        ('1', 'Корпус №1'),
        ('2', 'Корпус №2'),
        ('3', 'Корпус №3'),
        ('4', 'Корпус №4'),
        ('5', 'Корпус №5'),
        ('lux1', 'Корпус люкс №1'),
        ('lux2', 'Корпус люкс №2'),
        ('lux3', 'Корпус люкс №3'),
        ('lux4', 'Корпус люкс №4'),
    ]

    name = models.CharField("Наименование номера", max_length=100)
    capacity = models.PositiveIntegerField("Количество мест")
    floor = models.PositiveIntegerField("Этаж")
    building_type = models.CharField("Тип корпуса", max_length=10, choices=BUILDING_TYPE_CHOICES)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        # Можно показывать корпус тоже!
        bt = dict(self.BUILDING_TYPE_CHOICES).get(self.building_type, self.building_type)
        return f"{self.name} ({self.capacity} мест, этаж {self.floor}, {bt})"


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
    building_type = models.CharField("Тип корпуса", max_length=10, choices=RoomLayout.BUILDING_TYPE_CHOICES)

    # --- Полная стоимость ---
    price_full = models.DecimalField("Полная стоимость", max_digits=10, decimal_places=2)
    nds_full = models.DecimalField("НДС (полная)", max_digits=10, decimal_places=2, default=0)
    nma_full = models.DecimalField("НМА (полная)", max_digits=10, decimal_places=2, default=0)
    nsp_full = models.DecimalField("НСП (полная)", max_digits=10, decimal_places=2, default=0)

    # --- 50% стоимость ---
    price_50 = models.DecimalField("50% стоимость", max_digits=10, decimal_places=2)
    nds_50 = models.DecimalField("НДС (50%)", max_digits=10, decimal_places=2, default=0)
    nma_50 = models.DecimalField("НМА (50%)", max_digits=10, decimal_places=2, default=0)
    nsp_50 = models.DecimalField("НСП (50%)", max_digits=10, decimal_places=2, default=0)

    # --- Льготная стоимость: две опции, для каждой свои налоги ---
    price_lgot_1 = models.DecimalField("Льготная стоимость №1", max_digits=10, decimal_places=2)
    nds_lgot_1 = models.DecimalField("НДС (льготная 1)", max_digits=10, decimal_places=2, default=0)
    nma_lgot_1 = models.DecimalField("НМА (льготная 1)", max_digits=10, decimal_places=2, default=0)
    nsp_lgot_1 = models.DecimalField("НСП (льготная 1)", max_digits=10, decimal_places=2, default=0)

    price_lgot_2 = models.DecimalField("Льготная стоимость №2", max_digits=10, decimal_places=2)
    nds_lgot_2 = models.DecimalField("НДС (льготная 2)", max_digits=10, decimal_places=2, default=0)
    nma_lgot_2 = models.DecimalField("НМА (льготная 2)", max_digits=10, decimal_places=2, default=0)
    nsp_lgot_2 = models.DecimalField("НСП (льготная 2)", max_digits=10, decimal_places=2, default=0)

    LGOT_SET_CHOICES = [
        (1, 'Льготная №1'),
        (2, 'Льготная №2'),
    ]
    lgot_active_set = models.PositiveSmallIntegerField(
        "Активная льготная стоимость", choices=LGOT_SET_CHOICES, default=1
    )

    def get_active_lgot(self):
        if self.lgot_active_set == 1:
            return {
                "price": self.price_lgot_1,
                "nds": self.nds_lgot_1,
                "nma": self.nma_lgot_1,
                "nsp": self.nsp_lgot_1,
            }
        else:
            return {
                "price": self.price_lgot_2,
                "nds": self.nds_lgot_2,
                "nma": self.nma_lgot_2,
                "nsp": self.nsp_lgot_2,
            }

    def __str__(self):
        return self.name
