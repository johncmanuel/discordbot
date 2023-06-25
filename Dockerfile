FROM python:3.8.8

# /app will be default path for cmds 
WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

# Copy only the files needed to run the application
COPY app.py log.py config.py config.ini .env /app/
COPY src /app/src

CMD ["python", "app.py"]