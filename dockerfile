# используем образ с Python
FROM python:3.8-slim

# устанавливаем рабочую директорию в контейнере
WORKDIR /app

# копируем файлы зависимостей и устанавливаем их
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# копируем остальные файлы в контейнер
COPY . .

# команда для запуска вашего бота
CMD ["python", "app.py"]
