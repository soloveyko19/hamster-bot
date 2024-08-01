import requests
import fake_useragent


ua = fake_useragent.UserAgent()


class ClaimDailyRewardError(Exception):
    pass


class DailyRewardManager:
    tasks = list()

    def __init__(self, auth_key) -> None:
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
    
    def claim_reward(self):
        data = {
            "taskId": "streak_days"
        }
        response = requests.post(
            url="https://api.hamsterkombatgame.io/clicker/check-task",
            headers=self.headers,
            json=data
        )        
        if response.status_code != 200:
            raise ClaimDailyRewardError(response.content)
        
    def load_tasks(self):
        response = requests.post(
            url="https://api.hamsterkombatgame.io/clicker/list-tasks",
            headers=self.headers
        )
        if response.status_code != 200:
            raise ClaimDailyRewardError(response.content)
        self.tasks = response.json()["tasks"]
    
    @property
    def claimed(self) -> bool:
        for task in self.tasks:
            if task["id"] == "streak_days":
                return task["isCompleted"]
        return False
        
    def auto_mode(self):
        self.load_tasks()
        if self.claimed:
            raise ClaimDailyRewardError("Already claimed")
        self.claim_reward()



