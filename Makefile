.PHONY: run install test clean freeze migrate

run: 
	docker compose up --build --force-recreate

install:
	pip install -r requirements.txt

freeze:
	pip freeze > requirements.txt

test:
	PYTHONPATH=. pytest -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete