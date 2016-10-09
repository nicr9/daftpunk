all: push-dp2 build-web

push-dp2:
	python setup.py sdist upload -r pypi

build-web:
	docker build -t dp2:web -f web/Dockerfile web
