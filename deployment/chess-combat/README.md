# Helm Chart for chess-combat

This Helm chart deploys the chess-combat FastAPI application with Kubernetes best practices.

## Features
- Deploys the FastAPI app as a Kubernetes Deployment
- Exposes the app via a Service and a generic Ingress
- Uses Kubernetes Secrets for sensitive data (OpenAI, Gemini, Postgres)

## Usage

1. **Create secrets** (base64-encode your values):
   ```sh
   kubectl create secret generic openai-api-key --from-literal=api-key=<base64-openai-key>
   kubectl create secret generic gemini-api-key --from-literal=api-key=<base64-gemini-key>
   kubectl create secret generic postgres-connection --from-literal=connection=<base64-postgres-url>
   ```
   Or edit `templates/secrets.yaml` and apply with `kubectl apply -f` (not recommended for production).

2. **Install the chart:**
   ```sh
   helm install chess-combat ./deployment/chess-combat
   ```

3. **Access the app:**
   - The app will be available at the host configured in `values.yaml` (default: `chess-combat.local`).

## Configuration
See `values.yaml` for all configurable options.
