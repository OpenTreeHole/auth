import multiprocessing

from sanic import Sanic
from sanic.log import logger

app = Sanic('auth')

if app.config.get('DEBUG', True):
    logger.warning('\nserver is running in dev mode, do not use in production\n')

if __name__ == '__main__':
    from apis import app as server

    server.run(
        host='0.0.0.0',
        port=8000,
        workers=app.config.get('WORKERS', multiprocessing.cpu_count()),
        debug=app.config.get('DEBUG', True),
        access_log=app.config.get('ACCESS_LOG', True)
    )
