# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаём директорию для базы данных
RUN mkdir -p /app/data

# Переменные окружения (будут переопределены при запуске)
ENV BOT_TOKEN=""
ENV ADMIN_IDS=""
ENV DATABASE_PATH="/app/data/products.db"

# Запускаем бота
CMD ["python", "main.py"]