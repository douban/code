# coding=utf-8
from kombu import Queue

from vilya.config import REDIS_HOST, REDIS_PORT, REDIS_DB

BROKER_URL = 'redis://{0}:{1}/{2}'.format(REDIS_HOST, REDIS_PORT, REDIS_DB)
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TIMEZONE = 'UTC'

CELERY_IMPORTS = ('tasks', )

CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (
    Queue('default',    routing_key='task.#'),
    Queue('feed_tasks', routing_key='feed.#'),
)
CELERY_DEFAULT_EXCHANGE = 'tasks'
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = 'task.default'
CELERY_ROUTES = {
    'feeds.tasks.import_feed': {
        'queue': 'feed_tasks',
        'routing_key': 'feed.import',
    },
}
