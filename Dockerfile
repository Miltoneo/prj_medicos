# Use an official Python runtime as a parent image
FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install dependencies
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Instala utilitários de rede para depuração SMTP
RUN apt-get update && apt-get install -y iputils-ping netcat-openbsd

# Copy the project code into the container
COPY . /app
#CMD ["sh", "-c", "python manage.py migrate && gunicorn prj_medicos.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
