HUB_USER=nicr9

DP2_BASE=${HUB_USER}/dp2-base
DP2_WEB=${HUB_USER}/dp2-web
DP2_SCRIPTS=${HUB_USER}/dp2-scripts

WEB_SERVICE=daftpunk-web

# Build/publish

base-build:
	docker build -t ${DP2_BASE}:latest .

dp2-push:
	python setup.py sdist upload -r pypi

base-push:
	docker push ${DP2_BASE}:latest

web-build:
	docker build -t ${DP2_WEB}:latest -f web/Dockerfile web
	docker push ${DP2_WEB}:latest

web-rebuild:
	docker build -t ${DP2_WEB}:latest --no-cache -f web/Dockerfile web
	docker push ${DP2_WEB}:latest

scripts-build:
	docker build -t ${DP2_SCRIPTS}:latest -f scripts/Dockerfile scripts
	docker push ${DP2_SCRIPTS}:latest

scripts-rebuild:
	docker build -t ${DP2_SCRIPTS}:latest --no-cache -f scripts/Dockerfile scripts
	docker push ${DP2_SCRIPTS}:latest

publish-all: base-build dp2-push base-push web-rebuild scripts-rebuild

# Development environment

dev-build:
	docker-compose build

dev-rebuild: base-build
	docker-compose build --no-cache

dev-up:
	docker-compose up -d postgres redis
	sleep 10
	docker-compose up -d web

dev-post-up: dev-scripts-restore-cache

dev-replace:
	docker-compose up -d web

dev-down:
	docker-compose down

dev-psql:
	docker-compose exec postgres psql -U daftpunk -W

dev-redis:
	docker-compose exec redis redis-cli

dev-open:
	google-chrome --incognito 0.0.0.0:5000

dev-backend:
	docker-compose run scripts python backend.py

dev-scripts-retrieve-cache:
	docker-compose run scripts python cache.py retrieve

dev-scripts-backup-cache:
	docker-compose run scripts python cache.py backup
	docker cp `docker ps -lq`:/usr/src/app/data/cache.json scripts/data/

dev-scripts-flush-cache:
	docker-compose run scripts python cache.py flush

dev-scripts-restore-cache:
	docker-compose run scripts python cache.py restore

dev-scripts-update-questions:
	docker-compose run scripts python questions.py update

dev-scripts-flush-questions:
	docker-compose run scripts python questions.py flush

# Kubernetes environment

prod-build: web-build scripts-build
prod-rebuild: base-build web-rebuild scripts-rebuild

prod-up:
	kubectl apply -f manifests/daftpunk-configmap.yaml
	kubectl apply -f manifests/postgres-service.yaml
	kubectl apply -f manifests/postgres-pod.yaml
	kubectl apply -f manifests/redis-service.yaml
	kubectl apply -f manifests/redis-pod.yaml
	kubectl apply -f manifests/daftpunk-service.yaml
	kubectl apply -f manifests/daftpunk-deployment.yaml

prod-post-up: prod-scripts-restore-cache clean-jobs prod-backend

prod-down:
	kubectl delete -f manifests/daftpunk-configmap.yaml
	kubectl delete -f manifests/postgres-service.yaml
	kubectl delete -f manifests/postgres-pod.yaml
	kubectl delete -f manifests/redis-service.yaml
	kubectl delete -f manifests/redis-pod.yaml
	kubectl delete -f manifests/daftpunk-service.yaml
	kubectl delete -f manifests/daftpunk-deployment.yaml

prod-shell:
	kubectl run -it --image=alpine --rm sh --command -- /bin/sh

prod-web:
	kubectl exec -it `kubectl get po --selector app=flask --no-headers -o custom-columns=:.metadata.name` -- /bin/sh

prod-psql:
	kubectl exec -it daftpunk-postgres -- psql -U daftpunk -W

prod-redis:
	kubectl exec -it daftpunk-redis -- redis-cli

prod-open:
	google-chrome --incognito `minikube service ${WEB_SERVICE} --url`

prod-backend:
	kubectl apply -f manifests/backend-job.yaml

prod-scripts-retrieve-cache:
	sed \
		-e 's/SCRIPT/cache.py/g' \
		-e 's/CMD/retrieve/g' \
		manifests/scripts-job.yaml | kubectl create -f -

prod-scripts-backup-cache:
	sed \
		-e 's/SCRIPT/cache.py/g' \
		-e 's/CMD/backup/g' \
		manifests/scripts-job.yaml | kubectl create -f -
	#docker cp `docker ps -lq`:/usr/src/app/data/cache.json scripts/data/

prod-scripts-flush-cache:
	sed \
		-e 's/SCRIPT/cache.py/g' \
		-e 's/CMD/flush/g' \
		manifests/scripts-job.yaml | kubectl create -f -

prod-scripts-restore-cache:
	sed \
		-e 's/SCRIPT/cache.py/g' \
		-e 's/CMD/restore/g' \
		manifests/scripts-job.yaml | kubectl create -f -

# Utils

clean-jobs:
	kubectl get jobs --no-headers -o=custom-columns=NAME:.metadata.name | xargs kubectl delete jobs

install:
	sudo pip install -r requirements.txt
	sudo python setup.py develop

test:
	pytest tests -v
