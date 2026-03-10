# base image with python
FROM python:3.11-slim

# set workdir
WORKDIR /app

# copy only requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY . .

# default command
CMD ["python", "-m", "senpai_bot.main"]
