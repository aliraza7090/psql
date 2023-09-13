#FROM --platform=linux/amd64 python:3.10.5

FROM public.ecr.aws/i0t7e6o0/python3.10:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip3 install -r requirements.txt
COPY . .

EXPOSE 8000
#RUN python manage.py makemigrations
#RUN python manage.py migrate
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
