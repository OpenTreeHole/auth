from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from starlette.responses import RedirectResponse

app = FastAPI()  # app 实例化位于所有导入之前

from admin import permission, user
from auth import account, token

import oauth2

app.include_router(account.router, prefix='/api')
app.include_router(token.router, prefix='/api')
app.include_router(permission.router, prefix='/api')
app.include_router(user.router, prefix='/api')
app.include_router(oauth2.router, prefix='/api')


@app.get('/api')
async def home():
    return {'message': 'hello world'}


@app.get('/')
async def redirect_to_home():
    return RedirectResponse('/api')


@app.on_event('startup')
async def start_up():
    scheduler = AsyncIOScheduler()
    scheduler.start()
    scheduler.add_job(permission.sync_permissions, 'interval', seconds=3600)
