import requests
import time
from fake_useragent import UserAgent
import random
import base64

ua = UserAgent()

class ClaimError(Exception):
    pass

class MinigameManager:
    config = dict()

    def __init__(self, auth_key: str, tg_id: int):
        self.tg_id = tg_id
        self.headers = {
            "Authorization": auth_key,
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Origin': 'https://hamsterkombatgame.io',
            'Referer': 'https://hamsterkombatgame.io/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': ua.random,
            'accept': 'application/json',
            'content-type': 'application/json'
        }

    def load_config(self):
        response = requests.post(
            "https://api.hamsterkombatgame.io/clicker/config",
            headers=self.headers
        )
        if response.status_code != 200:
            raise Exception(response.content)
        self.config = response.json()

    @property
    def claimed(self) -> bool:
        if not self.config:
            raise ClaimError("Config not loaded")
        return self.config["dailyKeysMiniGame"]["isClaimed"]
    
    @property
    def unavailable(self) -> bool:
        if not self.config:
            raise ClaimError("Config not loaded")
        return self.config["dailyKeysMiniGame"]["remainSecondsToNextAttempt"] > 0

    
    def auto_mode(self):
        self.load_config()
        if self.claimed or self.unavailable:
            raise ClaimError("Already claimed or unavailable at the moment")
        self.start_game()
        time.sleep(random.randint(15, 27))
        self.claim_keys()

    def start_game(self):
        response = requests.post(
            "https://api.hamsterkombatgame.io/clicker/start-keys-minigame",
            headers=self.headers
        )
        if response.status_code != 200:
            raise ClaimError(response.content)

    @property
    def encoded_cipher(self) -> str:
        cipher = f"0300000000|{self.tg_id}"
        self.__encoded_cipher = base64.b64encode(cipher.encode()).decode()
        return self.__encoded_cipher

    def claim_keys(self):
        data = {
            "cipher": self.encoded_cipher
        }
        response = requests.post(
            url="https://api.hamsterkombatgame.io/clicker/claim-daily-keys-minigame",
            headers=self.headers,
            json=data
        )

        if response.status_code != 200:
            raise ClaimError(response.content)
        