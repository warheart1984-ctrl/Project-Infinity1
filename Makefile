.PHONY: run worker test

run:
	uvicorn app.main:app --reload

worker:
	celery -A app.celery_app.celery worker --loglevel=info

test:
	pytest -q
