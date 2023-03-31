FROM python:3.7-slim
LABEL maintainer="vladsolo23rus@gmail.com"
WORKDIR /app
COPY requirements.txt ./
RUN pip3 install -r requirements.txt --no-cache-dir
COPY ./ ./

#CMD ["gunicorn", "django_encommerce.wsgi:application", "--bind", "0:8000"]
#CMD ["python", "manage.py", "runserver", "0:8000"]