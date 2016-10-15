service=daftpunk-web

down:
	docker rm -f daftpunk-web || true

test: down
	docker run \
		-p 5000:5000 \
		-d \
		-e DAFT_USER=nicr9 \
		-e DAFT_PASSWD=XuX4h*keFLux \
		--name daftpunk-web \
		nicr9/dp2_web:latest

install: install-py build

install-py:
	python setup.py develop

push-py:
	python setup.py sdist upload -r pypi

build:
	docker build -t nicr9/dp2_web:latest -f web/Dockerfile web

push: build
	docker push nicr9/dp2_web:latest

deploy:
	kubectl apply -f manifests/daftpunk-configmap.yaml
	kubectl apply -f manifests/daftpunk-service.yaml
	kubectl apply -f manifests/daftpunk-deployment.yaml

teardown:
	kubectl delete -f manifests/daftpunk-configmap.yaml
	kubectl delete -f manifests/daftpunk-service.yaml
	kubectl delete -f manifests/daftpunk-deployment.yaml

open:
	google-chrome --incognito `minikube service ${service} --url`
