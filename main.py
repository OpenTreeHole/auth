from fastapi import FastAPI
from starlette.responses import RedirectResponse

app = FastAPI()  # app 实例化位于所有导入之前

from admin import punishment, user
from auth import account, token

app.include_router(account.router, prefix='/api')
app.include_router(token.router, prefix='/api')
app.include_router(punishment.router, prefix='/api')
app.include_router(user.router, prefix='/api')


@app.get('/api')
async def home():
    return {'message': 'hello world'}


@app.get('/')
async def redirect_to_home():
    return RedirectResponse('/api')
