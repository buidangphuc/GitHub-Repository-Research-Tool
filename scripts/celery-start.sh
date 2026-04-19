# work && beat
uv run python -m celery -A app.task.celery worker -l info -B

# flower
uv run python -m celery -A app.task.celery flower --port=8555 --basic-auth=admin:123456
