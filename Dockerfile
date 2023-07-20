# Установка базового образа
FROM python:3.10.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Установка рабочей директории
WORKDIR /app

# Установка зависимостей проекта в контейнер
COPY requirements.txt .

RUN pip install --upgrade pip

# Установка зависимостей проекта
RUN pip install -r requirements.txt

# Копирование файлов проекта в контейнер
COPY . .
