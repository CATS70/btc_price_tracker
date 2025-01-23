# src/btc_price_tracker.py
import asyncio
from binance import AsyncClient, BinanceSocketManager
from datetime import datetime
import pandas as pd
import os
from collections import defaultdict
from pathlib import Path


class PriceTracker:
    def __init__(self, symbol="btcusdt"):
        self.symbol = symbol
        self.second_prices = {}

        # Obtention du chemin du script courant
        current_file = Path(__file__)
        project_root = current_file.parent.parent

        # Utilisation du répertoire de données depuis la variable d'environnement ou chemin relatif au projet
        data_dir = os.getenv('DATA_DIR', str(project_root / 'data'))

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Construction du chemin complet du fichier
        filename = f'btc_prices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        self.prices_filename = self.data_dir / filename

        self.last_save_second = None
        print(f"Les données seront sauvegardées dans : {self.prices_filename}")

    async def initialize(self):
        self.client = await AsyncClient.create()
        self.bm = BinanceSocketManager(self.client)

    async def save_to_csv(self):
        """Sauvegarde les données dans le CSV"""
        if not self.second_prices:
            return

        data = [
            {
                'timestamp': ts,
                'first_price': prices[0],
                'last_price': prices[1]
            }
            for ts, prices in self.second_prices.items()
        ]
        df = pd.DataFrame(data)
        df = df.sort_values('timestamp')

        mode = 'w' if not os.path.exists(self.prices_filename) else 'a'
        header = not os.path.exists(self.prices_filename)

        df.to_csv(self.prices_filename, mode=mode, header=header, index=False)
        self.second_prices.clear()

    async def price_handler(self, msg):
        """Gère les messages du websocket"""
        try:
            price = float(msg['k']['c'])
            timestamp = int(msg['E'] / 1000)  # Conversion directe en secondes
            current_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

            if current_time not in self.second_prices:
                self.second_prices[current_time] = (price, price)
            else:
                self.second_prices[current_time] = (
                    self.second_prices[current_time][0],
                    price
                )

            print(f"[{current_time}] {self.symbol.upper()}: ${price:,.2f}")

            current_second = timestamp
            if self.last_save_second is None or current_second > self.last_save_second:
                await self.save_to_csv()
                self.last_save_second = current_second

        except Exception as e:
            print(f"Erreur dans le gestionnaire de prix: {e}")

    async def start(self):
        """Démarre le suivi des prix"""
        print(f"Démarrage du suivi {self.symbol.upper()}...")

        while True:
            try:
                ks = self.bm.kline_socket(symbol=self.symbol, interval='1s')
                async with ks as socket:
                    while True:
                        msg = await socket.recv()
                        await self.price_handler(msg)
            except Exception as e:
                print(f"Erreur de socket: {e}")
                print("Tentative de reconnexion dans 1 seconde...")
                await asyncio.sleep(1)

    async def cleanup(self):
        """Nettoie les ressources"""
        await self.client.close_connection()
        if self.second_prices:
            await self.save_to_csv()


async def main():
    tracker = PriceTracker()
    await tracker.initialize()

    try:
        await tracker.start()
    except KeyboardInterrupt:
        print("\nArrêt en cours...")
    finally:
        await tracker.cleanup()


if __name__ == "__main__":
    import signal


    def signal_handler(sig, frame):
        print("\nSignal d'arrêt reçu. Arrêt en cours...")
        loop.stop()


    loop = asyncio.get_event_loop()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()