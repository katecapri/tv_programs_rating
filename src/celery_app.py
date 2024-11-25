from celery import Celery
from kombu import Queue, Exchange, binding


app = Celery('default', include=['src.tasks.program_popularity_task',
                                 'src.tasks.user_preferences_task',
                                 'src.tasks.user_recommendations_task'])

app.config_from_object('src.config.settings', namespace='celery')

exchange = Exchange('default', type='direct')
app.conf.update(
    task_queues=(
        Queue('program_popularity', [binding(exchange, routing_key='program_popularity')]),
        Queue('user_preferences', [binding(exchange, routing_key='user_preferences')]),
        Queue('user_recommendations', [binding(exchange, routing_key='user_recommendations')]),
    )
)

app.conf.beat_schedule = {
    'program_popularity': {
        'task': 'src.tasks.program_popularity_task.calculate_program_popularity',
        'schedule': 60,
    },
    'user_preferences': {
        'task': 'src.tasks.user_preferences_task.calculate_user_segmentation_by_preferences',
        'schedule': 60,
    },
    'user_recommendations': {
        'task': 'src.tasks.user_recommendations_task.calculate_user_recommendations',
        'schedule': 60,
    },
}