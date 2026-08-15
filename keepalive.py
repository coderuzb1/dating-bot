import requests
import time
import threading
import os

URL = os.environ.get("RENDER_EXTERNAL_URL", "")

def keep_alive():
    if not URL:
        return
    while True:
        try:
            requests.get(URL, timeout=10)
        except:
            pass
        time.sleep(240)

threading.Thread(target=keep_alive, daemon=True).start()
