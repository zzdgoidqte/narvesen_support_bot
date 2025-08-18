FROM python:3.12

# Install PostgreSQL 16 client and locales
RUN apt-get update && \
    apt-get install -y wget gnupg lsb-release locales && \
    echo "lv_LV.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=lv_LV.UTF-8 && \
    wget --quiet -O /usr/share/keyrings/postgres.gpg https://www.postgresql.org/media/keys/ACCC4CF8.asc && \
    echo "deb [signed-by=/usr/share/keyrings/postgres.gpg] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list && \
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

# Copy rest of the app
COPY . .

# Start the app
CMD ["python", "main.py"]
