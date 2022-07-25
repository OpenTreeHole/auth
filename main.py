from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

app = FastAPI()  # app 实例化位于所有导入之前

from admin import permission, user
from auth import account, token

app.include_router(account.router)
app.include_router(token.router)
app.include_router(permission.router)
app.include_router(user.router)


@app.get('/')
async def home():
    return {'message': 'hello world'}


@app.on_event('startup')
async def start_up():
    scheduler = AsyncIOScheduler()
    scheduler.start()
    scheduler.add_job(permission.sync_permissions, 'interval', seconds=3600)
