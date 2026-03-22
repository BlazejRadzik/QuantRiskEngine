# Dockerfile
# Używamy oficjalnego obrazu Pythona
FROM python:3.11-slim

# Instalacja kompilatora C++ (G++) i OpenMP potrzebnego do silnika Monte Carlo
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopiowanie zależności i instalacja
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fpdf2 pybind11 torch torchvision torchaudio

# Kopiujemy kod projektu
COPY . .

# Kompilacja modułu C++ na Linuxie (.so zamiast .pyd) 
RUN python setup.py build_ext --inplace

# Kontener jest gotowy do odpalenia komend z docker-compose