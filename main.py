from fastapi import FastAPI

app = FastAPI()  # app 实例化位于所有导入之前

from admin import punishment, user
from auth import account, token

app.include_router(account.router)
app.include_router(token.router)
app.include_router(punishment.router)
app.include_router(user.router)


@app.get('/')
async def home():
    return {'message': 'hello world'}
