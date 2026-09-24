from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from datetime import datetime
from decimal import Decimal
import requests
from django.conf import settings

from .models import Tours, TourItems, Orders, OrderItems, Managers, Discount, Calendar


# ---------------------------------------------------------
# Главная страница
# ---------------------------------------------------------
def index2(request):
    tours = (
        Tours.objects
        .filter(is_active=True)
        .select_related('type_of_tour')
        .prefetch_related('items', 'calendar')
    )
    return render(request, 'index2.html', {
        'tours': tours, 
        'CF_TURNSTILE_SITE_KEY': settings.CF_TURNSTILE_SITE_KEY
    })

# ---------------------------------------------------------
# Детали тура
# ---------------------------------------------------------
def tour_detail(request, tour_id):
    tour = get_object_or_404(
        Tours.objects
        .select_related('type_of_tour')
        .prefetch_related('items', 'calendar')
        .filter(is_active=True),
        id=tour_id
    )
    return render(request, 'tour_detail.html', {
        'tour': tour,
        'items': tour.items.all(),
        'calendar': tour.calendar.filter(is_active=True),
    })


@require_POST
def booking_create(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не разрешён'}, status=405)
    # ---- 0. ПРОВЕРКА КАПЧИ (В САМОМ НАЧАЛЕ!) ----
    token = request.POST.get('cf-turnstile-response')
    secret_key = settings.CF_TURNSTILE_SECRET_KEY

    data = {
        'secret': secret_key,
        'response': token,
        'remoteip': request.META.get('REMOTE_ADDR')
    }
    r = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', data=data)
    result = r.json()

    if not result.get('success'):
        return JsonResponse(
            {'success': False, 'error': 'Проверка капчи не пройдена. Пожалуйста, попробуйте еще раз.'},
            status=400
        )
    # ---- 1. Получение и первичная валидация данных ----
    tour_id = request.POST.get('tour_id')
    date_str = request.POST.get('date')          # ожидаем YYYY-MM-DD
    consent = request.POST.get('consent')        # будет 'on', если чекбокс отмечен

    # ---- ВАЖНО: проверка согласия ----
    if not consent:
        error_msg = 'Необходимо дать согласие на обработку персональных данных'
        if _is_ajax(request):
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        else:
            messages.error(request, error_msg)
            return redirect('booking_step2')  # или ваш URL для шага 2

    try:
        adults = int(request.POST.get('adults', 0))
        children = int(request.POST.get('children', 0))
    except ValueError:
        return JsonResponse(
            {'success': False, 'error': 'Неверный формат количества участников'},
            status=400
        )

    guests = adults + children
    if not tour_id or not date_str or guests < 1:
        return JsonResponse(
            {'success': False, 'error': 'Неверные данные формы'},
            status=400
        )

    # ---- 2. Проверка существования тура и его цен ----
    tour = get_object_or_404(Tours, id=tour_id, is_active=True)
    item = tour.items.first()
    if not item:
        return JsonResponse(
            {'success': False, 'error': 'У тура нет ценовых данных'},
            status=400
        )

    cost_adult = item.cost_of_adult
    cost_child = item.cost_of_child if item.cost_of_child is not None else cost_adult

    # ---- 3. Проверка даты в календаре ----
    try:
        depart_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse(
            {'success': False, 'error': 'Неверный формат даты выезда'},
            status=400
        )

    if depart_date < timezone.now().date():
        return JsonResponse(
            {'success': False, 'error': 'Нельзя забронировать тур на прошедшую дату'},
            status=400
        )

    # Если нужна проверка по календарю – раскомментируйте
    # if not tour.calendar.filter(start_tour_date=depart_date, is_active=True).exists():
    #     return JsonResponse(
    #         {'success': False, 'error': 'Тур не проводится в выбранную дату'},
    #         status=400
    #     )

    # ---- 4. Расчёт базовой стоимости и скидки ----
    subtotal = (cost_adult * adults) + (cost_child * children)
    total_cost = subtotal

    active_discount = Discount.objects.filter(
        count_out__lte=guests,
        is_active=True
    ).order_by('-count_out').first()

    if active_discount:
        if active_discount.discount_percentage:
            total_cost = subtotal * (Decimal('1.00') - (active_discount.discount_percentage / Decimal('100.00')))
        elif active_discount.discount_cash:
            total_cost = max(Decimal('0.00'), subtotal - active_discount.discount_cash)

    # ---- 5. Получение данных участников ----
    first_names = request.POST.getlist('tourist_first_name')
    last_names = request.POST.getlist('tourist_last_name')
    middle_names = request.POST.getlist('tourist_middle_name')
    birthdays_str = request.POST.getlist('tourist_birthday')
    is_child_flags = request.POST.getlist('tourist_is_child')
    phones = request.POST.getlist('tourist_phone')
    emails = request.POST.getlist('tourist_email')

    if len(first_names) != guests or len(last_names) != guests:
        return JsonResponse(
            {'success': False, 'error': 'Заполните данные для всех участников'},
            status=400
        )

    adult_count = sum(1 for flag in is_child_flags if flag == '0')
    if len(phones) < adult_count:
        return JsonResponse(
            {'success': False, 'error': 'Не хватает телефонных номеров для взрослых участников'},
            status=400
        )

    participants = []
    adult_index = 0

    for i in range(guests):
        first = first_names[i].strip()
        last = last_names[i].strip()
        middle = middle_names[i].strip() if i < len(middle_names) else ''
        bday_str = birthdays_str[i].strip() if i < len(birthdays_str) else ''
        is_child_bool = is_child_flags[i] == '1' if i < len(is_child_flags) else False

        if not first or not last or not bday_str:
            return JsonResponse(
                {'success': False, 'error': f'Неполные данные участника #{i + 1}'},
                status=400
            )

        try:
            birthday = datetime.strptime(bday_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse(
                {'success': False, 'error': f'Неверная дата рождения участника #{i + 1}'},
                status=400
            )

        if birthday > timezone.now().date():
            return JsonResponse(
                {'success': False, 'error': f'Дата рождения участника #{i + 1} не может быть в будущем'},
                status=400
            )

        p_phone = None
        p_email = None
        if not is_child_bool:
            p_phone = phones[adult_index].strip() if adult_index < len(phones) else ''
            p_email = emails[adult_index].strip() if adult_index < len(emails) else ''
            adult_index += 1

            if not p_phone:
                return JsonResponse(
                    {'success': False, 'error': f'Укажите телефон для взрослого участника #{i + 1}'},
                    status=400
                )

        price_frozen = cost_child if is_child_bool else cost_adult

        participants.append({
            'first_name': first,
            'last_name': last,
            'middle_name': middle,
            'birthday': birthday,
            'is_child': is_child_bool,
            'price_frozen': price_frozen,
            'phone': p_phone,
            'email': p_email,
        })

    # ---- 6. Выбор менеджера ----
    manager = Managers.objects.filter(is_active=True).first()

    # ---- 7. Сохранение заказа (атомарная транзакция) ----
    try:
        with transaction.atomic():
            order = Orders.objects.create(
                tour=tour,
                tourists_count=guests,
                total_cost=total_cost,
                manager=manager,
                is_active=True,
                consent_to_personal_data=True   # <-- сохраняем согласие
            )

            for p in participants:
                OrderItems.objects.create(
                    order=order,
                    first_name=p['first_name'],
                    last_name=p['last_name'],
                    middle_name=p['middle_name'] or None,
                    birthday=p['birthday'],
                    phone=p['phone'],
                    email=p['email'],
                    is_child=p['is_child'],
                    price_frozen=p['price_frozen']
                )

        # ---- 8. Ответ ----
        if _is_ajax(request):
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'tour': tour.name,
                'date': date_str,
                'guests': guests,
                'total_cost': str(total_cost),
                'manager': {
                    'name': manager.name if manager else '',
                    'phone': manager.phone if manager else '',
                    'email': manager.email if manager else ''
                }
            })

        # Обычный POST – редирект на страницу заказа (или на успех)
        messages.success(request, 'Заказ успешно создан!')
        return redirect('order_detail', order_id=order.id)

    except Exception as e:
        # Логируйте ошибку, но пользователю показывайте общее сообщение
        return JsonResponse(
            {'success': False, 'error': 'Ошибка при сохранении заказа. Попробуйте позже.'},
            status=500
        )


# Вспомогательная функция для определения AJAX
def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

# ---------------------------------------------------------
# Детали заказа
# ---------------------------------------------------------
def order_detail(request, order_id):
    order = get_object_or_404(Orders, id=order_id, is_active=True)
    tourists = order.order_items.all()
    return render(request, 'order_detail.html', {'order': order, 'tourists': tourists})



# ---------------------------------------------------------
# Политика конфеденциальности
# ---------------------------------------------------------
def privacy_policy(request):
    tours = (
        Tours.objects
        .filter(is_active=True)
        .select_related('type_of_tour')
        .prefetch_related('items', 'calendar')
    )
    return render(request, 'privacy_policy.html', {
        'tours': tours,
        'CF_TURNSTILE_SITE_KEY': settings.CF_TURNSTILE_SITE_KEY
    })