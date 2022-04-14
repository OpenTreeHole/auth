from httpx import AsyncClient

from main import app

client = AsyncClient(app=app, base_url='http://test')
