from sanic import json

from server import app


@app.get('/')
async def home(request):
    return json({'message': 'hello world'})


@app.post('/login')
async def login(request):
    return json({})


@app.post('/register')
async def register(request):
    return json({})
