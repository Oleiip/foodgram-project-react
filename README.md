# API для проекта YaMDB в контейнере Docker
[![API for YaMDB project workflow](https://github.com/Oleiip/yamdb_final/actions/workflows/yamdb_workflow.yml/badge.svg?branch=main)](https://github.com/Oleiip/yamdb_final/actions/workflows/yamdb_workflow.yml)

[![Python](https://img.shields.io/badge/-Python-464646?style=flat-square&logo=Python)](https://www.python.org/)
[![Nginx](https://img.shields.io/badge/-NGINX-464646?style=flat-square&logo=NGINX)](https://nginx.org/ru/)
[![gunicorn](https://img.shields.io/badge/-gunicorn-464646?style=flat-square&logo=gunicorn)](https://gunicorn.org/)
[![docker](https://img.shields.io/badge/-Docker-464646?style=flat-square&logo=docker)](https://www.docker.com/)
[![GitHub%20Actions](https://img.shields.io/badge/-GitHub%20Actions-464646?style=flat-square&logo=GitHub%20actions)](https://github.com/features/actions)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat-square&logo=Yandex.Cloud)](https://cloud.yandex.ru/)
[![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)](https://www.django-rest-framework.org/)
[![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

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

Подробнее об установке на других платформах можно узнать на [официальном сайте](https://docs.docker.com/engine/install/).

Для начала необходимо скачать и выполнить официальный скрипт:
```bash
apt install curl
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

При необходимости удалить старые версии Docker:
```bash
apt remove docker docker-engine docker.io containerd runc 
```

Установить пакеты для работы через протокол https:
```bash
apt update
```
```bash
apt install \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg-agent \
  software-properties-common -y 
```

Добавить ключ GPG для подтверждения подлинности в процессе установки:
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```

Добавить репозиторий Docker в пакеты apt и обновить индекс пакетов:
```bash
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" 
```
```bash
apt update
```

Установить Docker(CE) и Docker Compose:
```bash
apt install docker-ce docker-compose -y
```

Проверить что  Docker работает можно командой:
```bash
systemctl status docker
```

Подробнее об установке можно узнать по [ссылке](https://docs.docker.com/engine/install/ubuntu/).

---
## 3. Переменные окружения <a id=3></a>

Проект использует базу данных PostgreSQL.  
Для подключения и выполненя запросов к базе данных необходимо создать и заполнить файл ".env" с переменными окружения в папке "./infra/".

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

Перед запуском необходимо склонировать проект:
```bash
HTTPS: git clone https://github.com/Oleiip/yamdb_final.git
SSH: git clone git@github.com:Oleiip/yamdb_final.git
```

Cоздать и активировать виртуальное окружение:
```bash
python -m venv venv
```
```bash
Linux: source venv/bin/activate
Windows: source venv/Scripts/activate
```

И установить зависимости из файла requirements.txt:
```bash
python3 -m pip install --upgrade pip
```
```bash
pip install -r requirements.txt
```
Далее необходимо собрать образы для фронтенда и бэкенда.  
Из папки "./backend/foodgram/" выполнить команду:
```bash
docker build -t oleiip/foodgram_backend .
```

Из папки "./frontend/" выполнить команду:
```bash
docker build -t oleiip/foodgram_frontend .
```

После создания образов можно создавать и запускать контейнеры.
Из папки "./infra/" выполнить команду создания и запуска контейнеров:
```bash
docker-compose up -d
```

После успешного запуска контейнеров выполнить миграции:
```bash
docker-compose exec web python manage.py makemigrations reviews
```
```bash
docker-compose exec web python manage.py migrate
```

Собрать статику:
```bash
docker-compose exec web python manage.py collectstatic --no-input 
```

---
## 5. Заполнение базы данных <a id=5></a>

Заполнить базу данных из файла с дампом:
```bash
docker-compose exec web python manage.py loaddata data/ingredients.json

```
Создать суперюзера:
```bash
docker-compose exec web python manage.py createsuperuser
```

---
## 6. После успешного деплоя <a id=6></a>

* Для проверки работоспособности приложения, перейти на страницу:
```
http://oleiip.sytes.net/admin/
```
## Документация для YaMDb доступна по адресу:
```
http://oleiip.sytes.net/redoc/
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