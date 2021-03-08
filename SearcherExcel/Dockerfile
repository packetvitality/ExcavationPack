# For more information, please refer to https://aka.ms/vscode-docker-python
# FROM ubuntu
FROM python:3.8-slim-buster

#Install packages
RUN apt-get -y update

# Setting the timezone so log files are timestamped correctly
# Change this to what you need if you want accurate timestamps :)
ENV TZ=America/Phoenix
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements
ADD requirements.txt .
RUN python3 -m pip install -r requirements.txt

WORKDIR /app
ADD . /app

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python3", "SearcherExcel.py"]
