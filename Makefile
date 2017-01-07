service=daftpunk-web

down:
	docker rm -f daftpunk-web || true

test: down
	docker run \
		-p 5000:5000 \
		-d \
		--name daftpunk-web \
		nicr9/dp2_web:latest

develop:
	sudo python setup.py develop

push-py:
	python setup.py sdist upload -r pypi

build:
	docker build -t nicr9/dp2_web:latest -f web/Dockerfile web
	docker push nicr9/dp2_web:latest

rebuild: push-py
	docker build -t nicr9/dp2_web:latest --no-cache -f web/Dockerfile web
	docker push nicr9/dp2_web:latest

deploy:
	kubectl apply -f manifests/daftpunk-configmap.yaml
	kubectl apply -f manifests/postgres-service.yaml
	kubectl apply -f manifests/postgres-pod.yaml
	kubectl apply -f manifests/redis-service.yaml
	kubectl apply -f manifests/redis-pod.yaml
	kubectl apply -f manifests/daftpunk-service.yaml
	kubectl apply -f manifests/daftpunk-deployment.yaml

teardown:
	kubectl delete -f manifests/daftpunk-configmap.yaml
	kubectl delete -f manifests/postgres-service.yaml
	kubectl delete -f manifests/postgres-pod.yaml
	kubectl delete -f manifests/redis-service.yaml
	kubectl delete -f manifests/redis-pod.yaml
	kubectl delete -f manifests/daftpunk-service.yaml
	kubectl delete -f manifests/daftpunk-deployment.yaml

open:
	google-chrome --incognito `minikube service ${service} --url`

shell:
	kubectl run -it --image=alpine --rm sh --command -- /bin/sh

python:
	kubectl run \
		-it --image=nicr9/dp2_web:latest --rm \
		sh -- python /usr/src/app/app.py

shell-flask:
	kubectl exec -it `kubectl get po --selector app=flask --no-headers -o custom-columns=:.metadata.name` -- /bin/sh

psql:
	kubectl exec -it daftpunk-postgres -- psql -U daftpunk -W

redis:
	kubectl exec -it daftpunk-redis -- redis-cli
