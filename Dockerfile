FROM python:3.11.11-slim

# Création d'un utilisateur non-root
RUN useradd -m -u 1000 btcuser

# Configuration du répertoire de travail
WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source et création du répertoire data
COPY src/ src/
RUN mkdir data && chown -R btcuser:btcuser /app

# Passage à l'utilisateur non-root
USER btcuser

# Définition des variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

# Commande de démarrage
CMD ["python", "src/btc_price_tracker.py"]