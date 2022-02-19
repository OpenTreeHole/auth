import multiprocessing

from sanic import Sanic
from sanic.log import logger

app = Sanic('auth')

if app.config.get('DEBUG', True):
    logger.warning('server is running in dev mode, do not use in production')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=app.config.get('PORT', 8000),
        workers=app.config.get('WORKERS', multiprocessing.cpu_count()),
        debug=app.config.get('DEBUG', True),
        access_log=app.config.get('ACCESS_LOG', True)
    )
