FROM python:3.10-slim

# C++ compiler install karne ke liye
RUN apt-get update && apt-get install -y \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Saari files copy karein
COPY . .

# Python dependencies install karein
RUN pip install --no-cache-dir -r requirements.txt

# C++ code ko compile karein (PRIME binary banane ke liye)
RUN g++ -O3 prime.cpp -o PRIME -pthread

# Permissions set karein
RUN chmod +x PRIME

# Bot ko start karein
CMD ["python", "PRIME.py"]
