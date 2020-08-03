FROM python:3.7

# don't create __pycache__ files
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /src

COPY ./ .
RUN pip install -r requirements.txt
