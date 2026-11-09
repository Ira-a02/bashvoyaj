# Баш Вояж — сайт туристической компании

Django-проект для туристической фирмы: каталог туров, бронирование,
админка, политика конфиденциальности.

🔗 **Демо:** [bashvoyaj.ru](https://bashvoyaj.ru) 


## 🛠 Стек

- Python 3.10+
- Django 4.2
- MySQL (production) / SQLite (development)
- Bootstrap 5
- JavaScript (AJAX, DOM)
- Cloudflare Turnstile

## ✨ Функционал

- Каталог туров с фильтрацией по категориям (горы, на воде, города, школьные туры, корпоративы)
- Форма бронирования с AJAX-отправкой без перезагрузки страницы
- Живой калькулятор стоимости с автоматической скидкой от 5 человек
- Капча Cloudflare Turnstile для защиты от спама
- Cookie-баннер с возможностью принять или отказаться
- Админка на Django Admin с кастомной настройкой полей
- Управление фото туров через админку
- Политика конфиденциальности в соответствии с 152-ФЗ
- Адаптивный дизайн (Bootstrap 5)

## 📦 Установка

```bash
git clone https://github.com/Ira-a02/bashvoyaj.git
cd bashvoyaj

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# заполните .env своими значениями

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Откройте [http://127.0.0.1:8000](http://127.0.0.1:8000).

## 🔐 Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DB_NAME=bashvoyaj
DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3306
CF_TURNSTILE_SITE_KEY=your-site-key
CF_TURNSTILE_SECRET_KEY=your-secret-key
```

## 📁 Структура проекта

```
bashvoyaj-portfolio/
│
├── core/
│   ├── migrations/
│   ├── management/commands/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── asgi.py
│   ├── models.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
│
├── templates/
│   ├── index2.html
│   └── privacy_policy.html
│
├── static/
│   ├── bootstrap-icons/
│   ├── css/
│   ├── docs/
│   ├── fonts/
│   ├── img/
│   └── js/
│
├── .env.example
├── .gitignore
├── manage.py
├── queries.sql
├── README.md
└── requirements.txt
```

## 🚀 Технические детали

- **Бронирование** реализовано через AJAX с `FormData` — без перезагрузки страницы.
- **Валидация** выполняется и на клиенте (JS), и на сервере (Django).
- **Капча** Cloudflare Turnstile проверяется на сервере перед созданием заказа.
- **Модели**: `Tours`, `TourItems`, `Orders`, `OrderItems`, `Managers`, `Calendar`, `Discount`.
- **Оптимизация**: `select_related` и `prefetch_related` для сокращения запросов к БД.
- **Статика** собирается через `collectstatic`, раздаётся через Nginx/Apache.


## 📄 Лицензия

Этот проект распространяется под лицензией MIT.
