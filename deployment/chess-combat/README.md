# Helm Chart for chess-combat

This Helm chart deploys the chess-combat FastAPI application with Kubernetes best practices.

## Features
- Deploys the FastAPI app as a Kubernetes Deployment
- Exposes the app via a Service and a generic Ingress
- Uses Kubernetes Secrets for sensitive data (OpenAI, Gemini, Postgres)
- Configurable security contexts and resource limits
- Built-in secret management through Helm values

## Usage

### Method 1: Using Helm Values (Recommended for Development)

1. **Install the chart with secrets:**
   ```sh
   helm install chess-combat ./deployment/chess-combat \
     --set secrets.openai.apiKey="your-openai-api-key" \
     --set secrets.gemini.apiKey="your-gemini-api-key" \
     --set secrets.postgres.connectionUrl="postgresql://user:password@host:5432/database"
   ```

2. **Or use a values file:**
   ```sh
   # Create a secret-values.yaml file:
   secrets:
     openai:
       apiKey: "your-openai-api-key"
     gemini:
       apiKey: "your-gemini-api-key"
     postgres:
       connectionUrl: "postgresql://user:password@host:5432/database"

   # Install with the values file:
   helm install chess-combat ./deployment/chess-combat -f secret-values.yaml
   ```

### Method 2: Using External Secrets (Recommended for Production/Flux)

1. **Create secrets externally (e.g., via Flux, External Secrets Operator, or manually):**
   ```yaml
   # Example Flux/Kubernetes secret
   apiVersion: v1
   kind: Secret
   metadata:
     name: chess-combat-openai
     namespace: default
   type: Opaque
   data:
     token: <base64-encoded-openai-key>
   ---
   apiVersion: v1
   kind: Secret
   metadata:
     name: chess-combat-postgres
     namespace: default
   type: Opaque
   data:
     url: <base64-encoded-postgres-url>
   ```

2. **Install the chart with external secret references:**
   ```sh
   helm install chess-combat ./deployment/chess-combat \
     --set secrets.openai.create=false \
     --set secrets.openai.secretName="chess-combat-openai" \
     --set secrets.openai.keyName="token" \
     --set secrets.gemini.create=false \
     --set secrets.gemini.secretName="chess-combat-gemini" \
     --set secrets.gemini.keyName="token" \
     --set secrets.postgres.create=false \
     --set secrets.postgres.secretName="chess-combat-postgres" \
     --set secrets.postgres.keyName="url"
   ```

3. **Or use a values file for external secrets:**
   ```yaml
   # external-secrets-values.yaml
   secrets:
     openai:
       create: false
       secretName: chess-combat-openai
       keyName: token
     gemini:
       create: false
       secretName: chess-combat-gemini
       keyName: token
     postgres:
       create: false
       secretName: chess-combat-postgres
       keyName: url
   ```

### Method 3: Manual Secret Creation (Legacy)

1. **Create secrets manually:**
   ```sh
   kubectl create secret generic openai-api-key --from-literal=api-key="your-openai-api-key"
   kubectl create secret generic gemini-api-key --from-literal=api-key="your-gemini-api-key"
   kubectl create secret generic postgres-connection --from-literal=connection="postgresql://user:password@host:5432/database"
   ```

2. **Install the chart using default secret names:**
   ```sh
   helm install chess-combat ./deployment/chess-combat \
     --set secrets.openai.create=false \
     --set secrets.gemini.create=false \
     --set secrets.postgres.create=false
   ```

### Access the Application

The app will be available at the host configured in `values.yaml` (default: `chess-combat.local`).

## Configuration

### Secret Configuration Options

Each secret can be configured independently:

```yaml
secrets:
  openai:
    create: true                    # Whether to create the secret via Helm
    secretName: "openai-api-key"    # Name of the secret in Kubernetes
    keyName: "api-key"              # Key name within the secret
    apiKey: ""                      # Value (only used if create=true)

  gemini:
    create: true
    secretName: "gemini-api-key"
    keyName: "api-key"
    apiKey: ""

  postgres:
    create: true
    secretName: "postgres-connection"
    keyName: "connection"
    connectionUrl: ""
```

### Other Configuration Options

See `values.yaml` for all configurable options including:
- Image repository and tag
- Service type and port
- Ingress configuration
- Security contexts
- Resource limits
- Secret management

## Security Notes

- Never commit actual secret values to version control
- Use separate values files for secrets in different environments
- Consider using external secret management tools like External Secrets Operator for production
