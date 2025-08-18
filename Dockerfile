FROM python:3.12

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg lsb-release locales curl ca-certificates && \
    echo "lv_LV.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=lv_LV.UTF-8 && \
    echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg && \
    apt-get update && \
    apt-get install -y postgresql-client-16 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=lv_LV.UTF-8
ENV LANGUAGE=lv_LV:lv
ENV LC_ALL=lv_LV.UTF-8

# Set working directory
WORKDIR /app

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Start the app
CMD ["python", "main.py"]
