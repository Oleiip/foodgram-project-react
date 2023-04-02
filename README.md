# API для проекта YaMDB в контейнере Docker
![foodgram-project-react workflow](https://github.com/Oleiip/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.7.0-blue?style=for-the-badge&logo=python&logoColor=yellow)
![Django](https://img.shields.io/badge/Django-2.2.19-red?style=for-the-badge&logo=django&logoColor=blue)
![Postgres](https://img.shields.io/badge/Postgres-13.0-blueviolet?style=for-the-badge&logo=postgresql&logoColor=yellow)
![Nginx](https://img.shields.io/badge/NGINX-1.19.3-orange?style=for-the-badge&logo=nginx&logoColor=green)
![Gunicorn](https://img.shields.io/badge/Gunicorn-20.1.0-inactive?style=for-the-badge&logo=gunicorn&logoColor=white)

# "Продуктовый помощник" (Foodgram)

## 1. [Описание](#1)
## 2. [Установка Docker (на платформе Ubuntu)](#2)
## 3. [База данных и переменные окружения](#3)
## 4. [Команды для запуска](#4)
## 5. [Заполнение базы данных](#5)
## 6. [После успешного деплоя](#6)
## 7. [Техническая информация](#7)

---
## 1. Описание <a id=1></a>

Проект "Продуктовый помошник" (Foodgram) предоставляет пользователям следующие возможности:
  - регистрироваться
  - создавать свои рецепты и управлять ими (корректировать\удалять)
  - просматривать рецепты других пользователей
  - добавлять рецепты других пользователей в "Избранное" и в "Корзину"
  - подписываться на других пользователей
  - скачать список ингредиентов для рецептов, добавленных в "Корзину"

---
## 2. Установка Docker (на платформе Ubuntu) <a id=2></a>

Проект поставляется в четырех контейнерах Docker (db, frontend, backend, nginx).  
Для запуска необходимо установить Docker и Docker Compose.  
Подробнее об установке на других платформах можно узнать на [официальном сайте](https://docs.docker.com/engine/install/).

* Выполните вход по ssh на удаленный сервер

* Выполните команды:
```
sudo apt update
sudo apt install docker.io
sudo apt install docker-compose
```

* Локально отредактируйте файл infra/nginx.conf и в строке server_name впишите свой IP
* Скопируйте файлы docker-compose.yml и nginx.conf из директории infra на сервер:
```
scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yml
scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
```
## 3. Переменные окружения <a id=3></a>

Проект использует базу данных PostgreSQL.  
Для подключения и выполнения запросов к базе данных необходимо создать и заполнить файл ".env" с переменными окружения в папке "./infra/" (ЛОКАЛЬНО). НА СЕРВЕРЕ ОН АВТОМАТИЧЕСКИ СОЗДАЕТСЯ foodgram_workflow.yml для этого нужно лишь добавить серкреты в settings > secrets and variables > actions

Шаблон для заполнения файла ".env":
```python
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY='Здесь указать секретный ключ'
```

---
## 4. Команды для запуска <a id=4></a>

Запуск контейнеров:
```bash
docker-compose up -d
```

После успешного запуска контейнеров выполнить миграции:
```bash
docker-compose exec backend python manage.py makemigrations
```
```bash
docker-compose exec backend python manage.py migrate
```

Собрать статику:
```bash
docker-compose exec backend python manage.py collectstatic --no-input 
```

---
## 5. Заполнение базы данных <a id=5></a>

Заполнить базу данных из файла с дампом:
```bash
docker-compose exec backend python manage.py loaddata data/ingredients.json

```
Создать суперюзера:
```bash
docker-compose exec backend python manage.py createsuperuser
```

---
## 6. После успешного деплоя <a id=6></a>

* Для проверки работоспособности приложения, перейти на страницу:
```
http://oleiip.sytes.net/admin/
```
## Документация для YaMDb доступна по адресу:
```
http://oleiip.sytes.net/api/docs/
```
---
## 7. Техническая информация <a id=7></a>

Стек технологий: Python 3, Django, Django Rest, React, Docker, PostgreSQL, nginx, gunicorn, Djoser.

Веб-сервер: nginx (контейнер nginx)  
Frontend фреймворк: React (контейнер frontend)  
Backend фреймворк: Django (контейнер backend)  
API фреймворк: Django REST (контейнер backend)  
База данных: PostgreSQL (контейнер db)

Веб-сервер nginx перенаправляет запросы клиентов к контейнерам frontend и backend, либо к хранилищам (volume) статики и файлов.  
Контейнер nginx взаимодействует с контейнером backend через gunicorn.  
Контейнер frontend взаимодействует с контейнером backend посредством API-запросов.

---
