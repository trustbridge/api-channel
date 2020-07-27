FROM python:3.6

# don't create __pycache__ files
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /src

COPY ./ .
RUN pip install flask
