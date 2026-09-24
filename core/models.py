import os
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


# -----------------------------
# Типы туров
# -----------------------------
class TypeOfTours(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Тип тура"
        verbose_name_plural = "Типы туров"

    def __str__(self):
        return self.name


# -----------------------------
# Основная модель тура
# -----------------------------
class Tours(models.Model):
    name = models.CharField(max_length=150)

    time_of_tour = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    start_date = models.DateField(null=True, blank=True)
    stop_date = models.DateField(null=True, blank=True)

    type_of_tour = models.ForeignKey(
        TypeOfTours,
        on_delete=models.PROTECT,
        related_name='tours'
    )

    description_short = models.CharField(max_length=500)

    photo = models.CharField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Тур"
        verbose_name_plural = "Туры"

    def save(self, *args, **kwargs):
        if self.start_date and self.time_of_tour:
            self.stop_date = self.start_date + timedelta(days=self.time_of_tour - 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# -----------------------------
# Детализация тура
# -----------------------------
class TourItems(models.Model):
    tour = models.ForeignKey(
        Tours,
        on_delete=models.CASCADE,
        related_name='items'
    )

    photo1 = models.FilePathField(
        path=os.path.join(settings.BASE_DIR, 'static', 'img'), #if hasattr(settings, 'BASE_DIR') else '',
        recursive=True,
        match=r'.*\.(jpg|jpeg|png|gif)$',
        max_length=255,
        blank=True,
        null=True
    )

    photo2 = models.FilePathField(
        path=os.path.join(settings.BASE_DIR, 'static', 'img'),
        recursive=True,
        match=r'.*\.(jpg|jpeg|png|gif)$',
        max_length=255,
        blank=True,
        null=True
    )

    photo3 = models.FilePathField(
        path=os.path.join(settings.BASE_DIR, 'static', 'img'),
        recursive=True,
        match=r'.*\.(jpg|jpeg|png|gif)$',
        max_length=255,
        blank=True,
        null=True
    )

    alt_photo1 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Alt для фото 1")
    alt_photo2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Alt для фото 2")
    alt_photo3 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Alt для фото 3")

    program_text = models.TextField(null=True, blank=True)

    cost_of_adult = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1)]
    )

    cost_of_child = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="Если оставить пустым — автоматически будет равна стоимости взрослого"
    )

    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Элемент тура"
        verbose_name_plural = "Элементы тура"

    def save(self, *args, **kwargs):
        if self.cost_of_child is None:
            self.cost_of_child = self.cost_of_adult
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Элемент тура: {self.tour.name}"


# -----------------------------
# Менеджеры
# -----------------------------
class Managers(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    # email = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Менеджер"
        verbose_name_plural = "Менеджеры"

    def __str__(self):
        return self.name


# -----------------------------
# Заказы
# -----------------------------
class Orders(models.Model):
    tour = models.ForeignKey(
        Tours,
        on_delete=models.PROTECT,
        related_name='orders'
    )

    order_date = models.DateTimeField(auto_now_add=True)
    tourists_count = models.IntegerField(validators=[MinValueValidator(1)])
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    manager = models.ForeignKey(
        Managers,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='orders'
    )

    is_active = models.BooleanField(default=True)

    delete_datetime = models.DateTimeField(null=True, blank=True)
    description_of_delete = models.CharField(max_length=500, null=True, blank=True)

    consent_to_personal_data = models.BooleanField(
        default=False,
        verbose_name="Согласие на обработку персональных данных"
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.id} — {self.tour.name}"


# -----------------------------
# Туристы в заказе
# -----------------------------
class OrderItems(models.Model):
    order = models.ForeignKey(
        Orders,
        on_delete=models.CASCADE,
        related_name='order_items'
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)

    birthday = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)

    price_frozen = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Цена продажи")
    is_child = models.BooleanField(default=False, verbose_name="Ребенок")

    class Meta:
        verbose_name = "Турист"
        verbose_name_plural = "Туристы"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# -----------------------------
# Календарь туров
# -----------------------------
class Calendar(models.Model):
    tour = models.ForeignKey(
        Tours,
        on_delete=models.CASCADE,
        related_name='calendar'
    )

    start_tour_date = models.DateField()
    return_tour_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Календарь"
        verbose_name_plural = "Календарь туров"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.return_tour_date < self.start_tour_date:
            raise ValidationError("Дата возврата не может быть раньше даты начала тура.")

    def __str__(self):
        return f"Календарь тура: {self.tour.name}"


# -----------------------------
# Скидки
# -----------------------------
class Discount(models.Model):
    count_out = models.IntegerField(validators=[MinValueValidator(1)], help_text="Количество людей для активации")

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01), MaxValueValidator(100)]
    )

    discount_cash = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)]
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Скидка"
        verbose_name_plural = "Скидки"


    def clean(self):
        if self.discount_percentage and self.discount_cash:
            raise ValidationError("Заполните только одно поле: либо процент, либо сумму скидки.")
        if not self.discount_percentage and not self.discount_cash:
            raise ValidationError("Необходимо заполнить либо процент, либо сумму скидки.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Принудительно вызываем clean() перед сохранением в БД
        super().save(*args, **kwargs)

    def __str__(self):
        if self.discount_percentage:
            return f"Скидка {self.discount_percentage}% (от {self.count_out} чел.)"
        return f"Скидка {self.discount_cash} руб. (от {self.count_out} чел.)"
















