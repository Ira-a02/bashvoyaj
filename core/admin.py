import os
from django import forms
from django.contrib import admin
from django.forms import NumberInput, TextInput
from django.conf import settings

from .models import (
    TypeOfTours,
    Tours,
    TourItems,
    Managers,
    Orders,
    OrderItems,
    Calendar,
    Discount
)

# ---------------------------------------------------------
#  Админка для Tours
# ---------------------------------------------------------
@admin.register(Tours)
class ToursAdmin(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "photo":
            img_path = os.path.join(settings.BASE_DIR, 'static', 'img')
            try:
                files = os.listdir(img_path)
                choices = [
                    (f"img/{file}", file)
                    for file in files
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))
                ]
            except FileNotFoundError:
                choices = []
            kwargs['widget'] = Select(choices=choices)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

# ---------------------------------------------------------
#  Форма для админки TourItems – переопределяем поля фото как CharField
# ---------------------------------------------------------
class TourItemsForm(forms.ModelForm):
    photo1 = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'size': 80, 'placeholder': 'img/путь/к/файлу.jpg'})
    )
    photo2 = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'size': 80, 'placeholder': 'img/путь/к/файлу.jpg'})
    )
    photo3 = forms.CharField(
        max_length=255,
        required=False,
        widget=TextInput(attrs={'size': 80, 'placeholder': 'img/путь/к/файлу.jpg'})
    )

    class Meta:
        model = TourItems
        fields = '__all__'

# ---------------------------------------------------------
#  Админка для TourItems — используем кастомную форму
# ---------------------------------------------------------
@admin.register(TourItems)
class TourItemsAdmin(admin.ModelAdmin):
    form = TourItemsForm

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Для цен оставляем NumberInput с шагом 100
        if db_field.name in ['cost_of_adult', 'cost_of_child']:
            kwargs['widget'] = NumberInput(attrs={'step': '100'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

# ---------------------------------------------------------
#  Inline для отображения участников внутри заказа
# ---------------------------------------------------------
class OrderItemsInline(admin.TabularInline):
    model = OrderItems
    extra = 0
    fields = ('last_name', 'first_name', 'middle_name', 'birthday', 'phone', 'email', 'is_child', 'price_frozen')
    readonly_fields = ('price_frozen',)

# ---------------------------------------------------------
#  Админка для Orders
# ---------------------------------------------------------
@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'tour', 'order_date', 'tourists_count',
        'total_cost', 'manager', 'is_active',
        'consent_to_personal_data'
    )
    list_filter = (
        'is_active', 'order_date', 'tour',
        'consent_to_personal_data'
    )
    search_fields = ('tour__name', 'id')
    readonly_fields = ('order_date', 'consent_to_personal_data')
    inlines = [OrderItemsInline]

# ---------------------------------------------------------
#  Остальные модели
# ---------------------------------------------------------
admin.site.register(TypeOfTours)
admin.site.register(Managers)
admin.site.register(Calendar)
admin.site.register(Discount)