import os
from dotenv import load_dotenv

load_dotenv()
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
URL_LOGIN = os.getenv('URL_LOGIN', 'https://lms.hcmut.edu.vn')
URL_CAS = os.getenv('URL_CAS', 'https://sso.hcmut.edu.vn/cas/login?service=')
TYPE_SSO = os.getenv('TYPE_SSO', 'CAS')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://discord.com/api/webhooks/')
TIME_SLEEP = int(os.getenv('TIME_SLEEP', 300))
HUGGINGFACE = os.getenv('HUGGINGFACE', 'false').lower()
HUGGINGFACE = True if HUGGINGFACE == 'true' else False