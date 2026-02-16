#starting from python base image
FROM python:3.11-slim

#set working directory
WORKDIR /app

#copy requirements file to the container
COPY requirements.txt .

# Install system packages
RUN apt-get update && apt-get install -y cron

# Install Python packages
RUN pip install -r requirements.txt

#copy all files to the container
COPY . .

#copy crontab file to the container
COPY crontab /etc/cron.d/collector-cron
RUN chmod 0644 /etc/cron.d/collector-cron
RUN crontab /etc/cron.d/collector-cron

RUN touch /var/log/collector.log

#start cron service
CMD printenv > /etc/environment && cron -f
