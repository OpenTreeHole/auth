from datetime import datetime

from config import config


def now():
    return datetime.now(config.tz)
