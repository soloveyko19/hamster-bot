import requests
import base64
from fake_useragent import UserAgent

ua = UserAgent()


class CipherManager:

    def __init__(self, auth_key: str) -> None:
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
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def load_cipher(self):
        response = requests.post(
            url="https://api.hamsterkombatgame.io/clicker/config",
            headers=self.headers
        )
        if response.status_code != 200:
            raise Exception(response.content)
        self.__encoded_cipher = response.json()["dailyCipher"]["cipher"]
        self.claimed = response.json()["dailyCipher"]["isClaimed"]
        self.encode_cipher()

    def claim_cipher(self) -> None:
        if not getattr(self, "cipher"):
            raise AttributeError("Attribute 'cipher' not set. Run method 'load_cipher' before the claim.")
        data = {
            "cipher": self.cipher
        }
        response = requests.post(
            url="https://api.hamsterkombatgame.io/clicker/claim-daily-cipher",
            headers=self.headers,
            json=data
        )
        if response.status_code != 200:
            raise Exception(response.content)

    def encode_cipher(self):
        cipher = self.__encoded_cipher[0:3] + self.__encoded_cipher[4:]
        self.cipher = base64.b64decode(cipher).decode()

    def auto_mode(self):
        self.load_cipher()
        if not self.claimed:
            self.claim_cipher()
        

