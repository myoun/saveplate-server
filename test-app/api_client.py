import requests
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None

    def login(self, username, password):
        logger.info("로그인 시도: %s", username)
        response = requests.post(f"{self.base_url}/token", data={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            logger.info("로그인 성공: %s", username)
            return True
        logger.error("로그인 실패: %s", username)
        return False

    def get_ingredients(self):
        logger.info("재료 목록 조회")
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/user/ingredients", headers=headers)
        if response.status_code == 200:
            logger.info("재료 목록 조회 성공")
            return response.json()
        logger.error("재료 목록 조회 실패")
        return []

    def add_ingredient(self, name, amount):
        logger.info("재료 추가 시도: %s, %d", name, amount)
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"ingredients": [{"name": name, "amount": amount}]}
        response = requests.post(f"{self.base_url}/user/ingredient", json=data, headers=headers)
        if response.status_code == 200:
            logger.info("재료 추가 성공: %s, %d", name, amount)
            return response.json()
        logger.error("재료 추가 실패: %s, %d", name, amount)
        return None

    def get_available_recipes(self):
        logger.info("가능한 레시피 조회")
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/recipes/available", headers=headers)
        if response.status_code == 200:
            logger.info("가능한 레시피 조회 성공")
            return response.json()
        logger.error("가능한 레시피 조회 실패")
        return []

    def get_autocomplete(self, type, prefix):
        logger.info("자동완성 조회: %s, %s", type, prefix)
        response = requests.get(f"{self.base_url}/autocompletion?type={type}&data={prefix}")
        if response.status_code == 200:
            logger.info("자동완성 조회 성공: %s, %s", type, prefix)
            return response.json()
        logger.error("자동완성 조회 실패: %s, %s", type, prefix)
        return []

    def register(self, email, password, name, gender, birth_date):
        logger.info("회원가입 시도: %s", email)
        data = {
            "email": email,
            "password": password,
            "name": name,
            "gender": gender,
            "birth_date": birth_date
        }
        response = requests.post(f"{self.base_url}/auth/register", json=data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            logger.info("회원가입 성공: %s", email)
            return True
        logger.info("실패 사유: %s", response.text)
        logger.error("회원가입 실패: %s", email)
        return False
