# eCommerce Project 

----

## 📄 Описание проекта
Django eCommerce - это полнофункциональный интернет-магазин, который обеспечивает легкий и удобный процесс покупок для клиентов. Регистрация на сайте реализована через библиотеку django-allauth. 

На странице оформления заказа пользователи могут указать место для доставки и выбрать оплату через сервис Stripe. Это обеспечивает безопасную и удобную оплату онлайн с помощью кредитных карт.

В случае, если клиент по ошибке совершил платеж или не удовлетворен качеством товара, он может перейти в свой профиль, выбрать нужный заказ и оформить возврат средств.

## 🔧 Стек технологий
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org)
[![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)
![Bootstrap](https://img.shields.io/badge/bootstrap-%23563D7C.svg?style=for-the-badge&logo=bootstrap&logoColor=white)

- Python 3.7
- Django 2.2 LTS
- JavaScript
- PostgreSQL
- Docker
- Stripe


## Наполнение .env файла для работы проекта
- Без Docker (PostgreSQL / SQLite)
  - [.env-local](.env.example-local)
- C Docker 
  - [env-prod](.env.example-prod)

### Подробнее о ключах Stripe
- Необходимо зарегистрироваться на сайте
- Для получения ключей нужно пройти процесс аутентификации
- Получить тестовые ключи
![Stripe](readme_images/stripe.png)

-------------

# Как запустить проект без Docker

1) Клонировать репозиторий
```shell
git clone git@github.com:Dazzy132/Django-eCommerce.git
```

2) Создать и активировать виртуальное окружение
```shell
python -m venv venv

source venv/Scripts/activate (Для Windows)
source venv/bin/activate (Для Linux и MacOS)
```
3)  Установить зависимости
```shell
pip install -r requirements.txt
```
4) Выполнить миграции
```shell
python manage.py makemigrations
python manage.py migrate
```
5) Создать суперпользователя (Рекомендуется)
```shell
python manage.py createsuperuser --username=root --email=root@mail.ru
```

6) Запустить сервер
```shell
python manage.py runserver
```

# Как запустить проект с Docker

```shell
cd infra
docker-compose up -d
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic
docker-compose exec web python manage.py createsuperuser --username=root --email=root@mail.ru
```

-----------------

# Как выглядит сайт


![Скрин](readme_images/1.png)
![Скрин](readme_images/2.png)
![Скрин](readme_images/3.png)
![Скрин](readme_images/4.png)
![Скрин](readme_images/5.png)
![Скрин](readme_images/6.png)
![Скрин](readme_images/7.png)