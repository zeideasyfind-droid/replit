FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create output dir
RUN mkdir -p output

EXPOSE 8080

CMD ["python", "main.py"]
