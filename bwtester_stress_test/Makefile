seed:
	python scion-seed.py
docker:
	cd seed-compiled && docker compose build && docker compose up
graphviz:
	cd viz && dot -Tpng Scion\ Connections.dot -o scion.png
all: seed graphviz docker
clean: clean-logs
	cd seed-compiled && docker compose down
	rm -rf seed-compiled
	rm -rf viz
	rm asns
clean-logs:
	rm -rf logs

docker-down:
	cd seed-compiled && docker compose down
	
docker-up:
	cd seed-compiled && docker compose up -d

down: docker-down clean-logs

logs:
	python makeLogFolders.py

up: logs docker-up

save_logs:
	zip -r logs.zip logs