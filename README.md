# chess-combat

## Logging and Debug Features

The application includes comprehensive logging to help you monitor and debug chess game behavior. Logs are displayed on the console with detailed information about:

- Application startup and shutdown
- Database operations (player creation, game creation, moves)
- AI API calls (OpenAI and Gemini)
- Chess move validation and execution
- HTTP endpoints and API calls

### Enabling Debug Mode

To see detailed debug logs, set the `DEBUG` environment variable:

```bash
# Linux/Mac
export DEBUG=true
uvicorn app.main:app --reload

# Or inline
DEBUG=true uvicorn app.main:app --reload
```

### Log Levels

- **INFO**: General application flow, successful operations
- **DEBUG**: Detailed information for debugging (requires DEBUG=true)
- **WARNING**: Recoverable issues (invalid moves, fallback operations)
- **ERROR**: Serious problems that need attention

## Setup and Running



To build this


Run a postgres docker container

docker network create chess-net
docker run --name chess-postgres --network chess-net -e POSTGRES_USER=chess -e POSTGRES_PASSWORD=chess -e POSTGRES_DB=chess -p 5432:5432 -d postgres:16


docker run --env OPENAI_API_KEY='<secret key goes here>' --env DATABASE_URL="postgresql://chess:chess@chess-postgres:5432/chess" --network chess-net -p 8000:8000 chess-combat


To run the application locally directly from code

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload


For Powershell
# 1. Create the venv
python -m venv .venv

# 2. Activate it (dot-source the Activate.ps1 script)
. .\.venv\Scripts\Activate.ps1

# 3. Install your requirements
pip install -r requirements.txt




URL for swagger endpoint. There is no UI yet.  😊
http://127.0.0.1:8000/docs#/default




Teodor ... Når du starter

. .\.venv\Scripts\Activate.ps1
$ENV:OPENAI_API_KEY=<openapikey>
Start docker-desktop
og start postgres container med
docker start chess-postgres



For at se ting i databasen
winget install DBeaver.DBeaver.Community