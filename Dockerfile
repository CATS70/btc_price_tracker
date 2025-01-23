FROM python:3.9-slim

# Création d'un utilisateur non-root avec un UID/GID spécifique
RUN useradd -u 1000 -U -m -s /bin/bash btcuser

# Configuration du répertoire de travail
WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source et création du répertoire data
COPY src/ src/
RUN mkdir data && \
    chown -R btcuser:btcuser /app && \
    chmod -R 755 /app/src && \
    chmod 777 /app/data

# Passage à l'utilisateur non-root
USER btcuser

# Définition des variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

# Commande de démarrage
CMD ["python", "src/btc_price_tracker.py"]