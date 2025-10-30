# Foodgram

Финальный проект учебного курса бэкенд-разработчика от Яндекс.Практикума.

## Адрес сайта
IP-адрес сервера: 84.252.137.104

[https://foogram4ik.ddns.net/](https://foogram4ik.ddns.net/)

## Админка сайта

Логин: review@admin.ru

Пароль: review1admin

[Авторизоваться](https://foodforjpg.publicvm.com/admin/login/?next=/admin/)

## Описание проекта
Foodgram - социальная сеть для публикации рецептов приготовления блюд. Любой желающий может зарегистрироваться и опубликовать свои рецепты, просматривать рецепты других авторов, подписываться на их публикации и добавлять их рецепты к себе в избранное.

## Используемые технологии
<p align="center">

<img src="https://img.shields.io/badge/Python-3.9-green">

<img src="https://img.shields.io/badge/django-3.2.3-green">

<img src="https://img.shields.io/badge/DRF-3.12.4-red">

</p>

## Развертывание проекта на локальном компьютере:

#### Шаг 1: Клонировать репозиторий и перейти в директорию бэкенда проекта

```shell
 clone git@github.com:sxmething/foodgram.git
```

```shell
cd foodgram/backend
```

#### Шаг 2: Создать и активировать виртуальное окружение

```shell
python -m venv venv
```

```shell
source venv/bin/activate
```

#### Шаг 3: Установить зависимости проекта


```shell
pip install -r requirements.txt
```

#### Шаг 4: Сгенерировать и скопировать SECRET_KEY

```shell
python manage.py shell
```
```shell
from django.core.management import utils
```
```shell
utils.get_random_secret_key()
```

#### Шаг 5: Создать файл `.env` с переменными окружения

```shell
touch .env
```

###### Необходимые переменные:

```shell
SECRET_KEY=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
DB_NAME=
DB_HOST=
DB_PORT=
DEBUG_MODE=
HASHIDS_SALT=
ALLOWED_HOSTS=
```
#### Шаг 6: Примененить миграции
```shell
python manage.py migrate
```

#### Шаг 7: Загрузить справочник ингридиентов в базу данных

```shell
python manage.py import_from_csv
```

#### Шаг 8: Запустить сервер

```shell
python manage.py runserver
```