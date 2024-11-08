FROM python:3.12

WORKDIR /code

COPY . /code

RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "8080", "--proxy-headers"]