import time
import requests


def create_user(self, email: str, password: str) -> bool:
    auth_request = requests.post(f'http://{self.server}/users', {
        'email': email,
        'password': password
    })
    response = auth_request.json()
    if 'email' in response:
        return True
    else:
        return False


class Auth:
    def __init__(self, server: str, username: str, password: str, logging: bool = True):
        self.token: str
        self.exp: int
        self.server = server
        self.username = username
        self.password = password
        self.logging = logging
        self.first_auth()

    def timestamp_expired(self):
        now = int(time.time())
        if hasattr(self, 'exp'):
            expired = now >= self.exp or (now + 3600) >= self.exp
            if expired:
                return True
            else:
                return False
        else:
            return True

    def first_auth(self):
        while True:
            try:
                myauth = self.auth()
                if myauth:
                    break
            except requests.exceptions.ConnectionError:
                print('Could not connect to server. Waiting...')
                time.sleep(1)

    def auth(self, force: bool = False) -> str:
        timestamp_expired = self.timestamp_expired()
        if not timestamp_expired:
            return self.token

        auth_request = requests.post(f'http://{self.server}/authentication', {
            'strategy': 'local',
            'email': self.username,
            'password': self.password
        })
        response = auth_request.json()
        if self.logging:
            print("Authenticated")
        self.token = response['accessToken']
        self.exp = response['authentication']['payload']['exp']

        return self.token
