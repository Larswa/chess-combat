# chess-combat



To build this


Run a postgres docker container
docker run --name chess-postgres -e POSTGRES_USER=chess -e POSTGRES_PASSWORD=chess -e POSTGRES_DB=chess -p 5432:5432 -d postgres:16


python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt