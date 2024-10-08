import logging
from gui import App
from api_client import APIClient
import os
import dotenv

dotenv.load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    api_client = APIClient(os.getenv("SERVER_URL"))  # 백엔드 서버 URL을 적절히 변경하세요
    app = App(api_client)
    app.mainloop()
