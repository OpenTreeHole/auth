import multiprocessing

from sanic import Sanic
from sanic.response import json

app = Sanic('auth')


@app.get('/')
async def home(request):
    return json({'message': 'hello world'})


@app.post('/login')
async def login(request):
    return json({})


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=app.config.get('PORT', 8000),
        workers=app.config.get('WORKERS', multiprocessing.cpu_count()),
        debug=app.config.get('DEBUG', False),
        access_log=app.config.get('ACCESS_LOG', True)
    )
