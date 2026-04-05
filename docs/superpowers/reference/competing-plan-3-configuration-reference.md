# Venus Forum Integration - Configuration Reference

> **Source**: External configuration reference, accompanies competing plans 1 and 2.
> **Status**: Reference only — not adopted. See analysis in `competing-plans-analysis.md`.

---

## Contents
1. Docker Compose Configuration
2. Kubernetes Deployment
3. Nginx Ingress Configuration
4. Keycloak Realm Configuration
5. Pulsar Topic Configuration
6. Environment Variables Template

---

## 1. DOCKER COMPOSE CONFIGURATION

```yaml
version: '3.8'

services:
  # Forum Strapi CMS
  forum-strapi:
    image: venus/forum-strapi:latest
    container_name: forum-strapi
    ports:
      - "1338:1338"
    environment:
      - NODE_ENV=production
      - DATABASE_CLIENT=postgres
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=forum_strapi
      - DATABASE_USERNAME=${DB_USER}
      - DATABASE_PASSWORD=${DB_PASSWORD}
      - JWT_SECRET=${STRAPI_JWT_SECRET}
      - ADMIN_JWT_SECRET=${STRAPI_ADMIN_JWT_SECRET}
      - API_TOKEN_SALT=${STRAPI_API_TOKEN_SALT}
      - APP_KEYS=${STRAPI_APP_KEYS}
      - KEYCLOAK_URL=${KEYCLOAK_URL}
      - KEYCLOAK_REALM=venus-platform
      - KEYCLOAK_CLIENT_ID=venus-forum-client
      - PULSAR_SERVICE_URL=${PULSAR_SERVICE_URL}
    volumes:
      - forum-uploads:/app/public/uploads
      - ./forum-strapi/config:/app/config
    depends_on:
      - postgres
      - keycloak
    networks:
      - venus-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:1338/admin"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Forum BFF Service
  forum-bff:
    image: venus/forum-bff:latest
    container_name: forum-bff
    ports:
      - "4001:4001"
    environment:
      - NODE_ENV=production
      - PORT=4001
      - FORUM_STRAPI_URL=http://forum-strapi:1338
      - FORUM_STRAPI_API_TOKEN=${STRAPI_API_TOKEN}
      - VENUS_BFF_URL=http://venus-bff:4000
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_DB=0
      - PULSAR_SERVICE_URL=${PULSAR_SERVICE_URL}
      - PULSAR_TOKEN=${PULSAR_TOKEN}
      - KEYCLOAK_URL=${KEYCLOAK_URL}
      - KEYCLOAK_CLIENT_ID=venus-bff-client
      - KEYCLOAK_CLIENT_SECRET=${KEYCLOAK_BFF_SECRET}
      - RATE_LIMIT_WINDOW_MS=60000
      - RATE_LIMIT_MAX_REQUESTS=100
    depends_on:
      - forum-strapi
      - redis
      - pulsar
    networks:
      - venus-network
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  # WebSocket Server
  forum-ws:
    image: venus/forum-ws:latest
    container_name: forum-ws
    ports:
      - "4002:4002"
    environment:
      - NODE_ENV=production
      - PORT=4002
      - REDIS_URL=redis://redis:6379
      - PULSAR_SERVICE_URL=${PULSAR_SERVICE_URL}
      - PULSAR_TOKEN=${PULSAR_TOKEN}
      - ALLOWED_ORIGINS=https://venus.com,https://www.venus.com
    depends_on:
      - redis
      - pulsar
    networks:
      - venus-network
    deploy:
      replicas: 2

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: forum-postgres
    ports:
      - "5433:5432"
    environment:
      - POSTGRES_DB=forum_strapi
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - venus-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: forum-redis
    ports:
      - "6380:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - venus-network

  # Pulsar (using standalone for dev)
  pulsar:
    image: apachepulsar/pulsar:3.0.0
    container_name: forum-pulsar
    ports:
      - "6650:6650"
      - "8080:8080"
    environment:
      - PULSAR_MEM=-Xms512m -Xmx512m
    command: bin/pulsar standalone
    volumes:
      - pulsar-data:/pulsar/data
    networks:
      - venus-network

volumes:
  forum-uploads:
  postgres-data:
  redis-data:
  pulsar-data:

networks:
  venus-network:
    external: true
```

---

## 2. KUBERNETES DEPLOYMENT

```yaml
# Forum Strapi Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: forum-strapi
  namespace: venus-services
  labels:
    app: forum-strapi
spec:
  replicas: 2
  selector:
    matchLabels:
      app: forum-strapi
  template:
    metadata:
      labels:
        app: forum-strapi
    spec:
      containers:
        - name: forum-strapi
          image: venus/forum-strapi:latest
          ports:
            - containerPort: 1338
          env:
            - name: NODE_ENV
              value: "production"
            - name: DATABASE_CLIENT
              value: "postgres"
            - name: DATABASE_HOST
              valueFrom:
                secretKeyRef:
                  name: forum-db-secret
                  key: host
            - name: DATABASE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: forum-db-secret
                  key: password
            - name: JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: forum-strapi-secret
                  key: jwt-secret
            - name: KEYCLOAK_URL
              valueFrom:
                configMapKeyRef:
                  name: venus-config
                  key: keycloak-url
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /admin
              port: 1338
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /admin
              port: 1338
            initialDelaySeconds: 5
            periodSeconds: 5
          volumeMounts:
            - name: uploads
              mountPath: /app/public/uploads
      volumes:
        - name: uploads
          persistentVolumeClaim:
            claimName: forum-uploads-pvc
---
# Forum Strapi Service
apiVersion: v1
kind: Service
metadata:
  name: forum-strapi
  namespace: venus-services
spec:
  selector:
    app: forum-strapi
  ports:
    - port: 1338
      targetPort: 1338
  type: ClusterIP
---
# Forum BFF Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: forum-bff
  namespace: venus-bff
  labels:
    app: forum-bff
spec:
  replicas: 3
  selector:
    matchLabels:
      app: forum-bff
  template:
    metadata:
      labels:
        app: forum-bff
    spec:
      containers:
        - name: forum-bff
          image: venus/forum-bff:latest
          ports:
            - containerPort: 4001
          env:
            - name: NODE_ENV
              value: "production"
            - name: PORT
              value: "4001"
            - name: FORUM_STRAPI_URL
              value: "http://forum-strapi.venus-services.svc.cluster.local:1338"
            - name: REDIS_HOST
              valueFrom:
                secretKeyRef:
                  name: redis-secret
                  key: host
            - name: PULSAR_SERVICE_URL
              valueFrom:
                configMapKeyRef:
                  name: venus-config
                  key: pulsar-url
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "300m"
---
# Forum BFF Service
apiVersion: v1
kind: Service
metadata:
  name: forum-bff
  namespace: venus-bff
spec:
  selector:
    app: forum-bff
  ports:
    - port: 4001
      targetPort: 4001
  type: ClusterIP
---
# HPA for Forum BFF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: forum-bff-hpa
  namespace: venus-bff
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: forum-bff
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## 3. NGINX INGRESS CONFIGURATION

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: venus-forum-ingress
  namespace: venus-frontend
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
    - hosts:
        - venus.com
        - www.venus.com
      secretName: venus-tls
  rules:
    - host: venus.com
      http:
        paths:
          - path: /forum
            pathType: Prefix
            backend:
              service:
                name: astro-app
                port:
                  number: 3000
          - path: /api/forum
            pathType: Prefix
            backend:
              service:
                name: forum-bff
                port:
                  number: 4001
          - path: /ws
            pathType: Prefix
            backend:
              service:
                name: forum-ws
                port:
                  number: 4002
          - path: /sitemap-forum.xml
            pathType: Exact
            backend:
              service:
                name: forum-bff
                port:
                  number: 4001
---
# WebSocket Ingress with sticky sessions
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: venus-ws-ingress
  namespace: venus-services
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/connection-proxy-header: "upgrade"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$binary_remote_addr"
spec:
  rules:
    - host: ws.venus.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: forum-ws
                port:
                  number: 4002
```

---

## 4. KEYCLOAK REALM CONFIGURATION

```json
{
  "realm": "venus-platform",
  "enabled": true,
  "displayName": "Venus Platform",
  "sslRequired": "external",
  "registrationAllowed": true,
  "registrationEmailAsUsername": false,
  "rememberMe": true,
  "verifyEmail": true,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "resetPasswordAllowed": true,
  "editUsernameAllowed": false,
  "bruteForceProtected": true,
  "permanentLockout": false,
  "maxFailureWaitSeconds": 900,
  "minimumQuickLoginWaitSeconds": 60,
  "waitIncrementSeconds": 60,
  "quickLoginCheckMilliSeconds": 1000,
  "maxDeltaTimeSeconds": 43200,
  "failureFactor": 5,

  "roles": {
    "realm": [
      { "name": "forum-user", "description": "Basic forum user permissions" },
      { "name": "forum-moderator", "description": "Forum moderator with elevated permissions" },
      { "name": "forum-admin", "description": "Full forum administration access" },
      { "name": "forum-banned", "description": "Banned from forum participation" }
    ]
  },

  "clients": [
    {
      "clientId": "venus-forum-client",
      "name": "Venus Forum Client",
      "description": "Forum application client for web and mobile",
      "enabled": true,
      "clientAuthenticatorType": "client-secret",
      "secret": "${FORUM_CLIENT_SECRET}",
      "redirectUris": [
        "https://venus.com/forum/*",
        "https://venus.com/auth/callback",
        "https://www.venus.com/forum/*",
        "https://www.venus.com/auth/callback"
      ],
      "webOrigins": ["https://venus.com", "https://www.venus.com"],
      "standardFlowEnabled": true,
      "implicitFlowEnabled": false,
      "directAccessGrantsEnabled": true,
      "serviceAccountsEnabled": false,
      "publicClient": false,
      "frontchannelLogout": true,
      "protocol": "openid-connect",
      "attributes": {
        "access.token.lifespan": "300",
        "refresh.token.lifespan": "1800",
        "id.token.signed.response.alg": "RS256",
        "access.token.signed.response.alg": "RS256"
      },
      "protocolMappers": [
        {
          "name": "forum_nickname",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-usermodel-attribute-mapper",
          "config": {
            "user.attribute": "forum_nickname",
            "claim.name": "forum_nickname",
            "jsonType.label": "String",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true"
          }
        },
        {
          "name": "forum_roles",
          "protocol": "openid-connect",
          "protocolMapper": "oidc-usermodel-realm-role-mapper",
          "config": {
            "claim.name": "forum_roles",
            "multivalued": "true",
            "id.token.claim": "true",
            "access.token.claim": "true",
            "userinfo.token.claim": "true"
          }
        }
      ]
    }
  ],

  "userProfile": {
    "attributes": [
      {
        "name": "forum_nickname",
        "displayName": "Forum Nickname",
        "validations": {
          "length": { "min": 3, "max": 30 },
          "pattern": {
            "pattern": "^[a-zA-Z0-9_]+$",
            "error-message": "Nickname can only contain letters, numbers, and underscores"
          }
        },
        "permissions": {
          "view": ["admin", "user"],
          "edit": ["admin", "user"]
        },
        "required": {
          "roles": ["forum-user"]
        }
      },
      {
        "name": "forum_avatar",
        "displayName": "Forum Avatar URL",
        "validations": { "uri": {} },
        "permissions": {
          "view": ["admin", "user"],
          "edit": ["admin", "user"]
        }
      },
      {
        "name": "forum_reputation",
        "displayName": "Forum Reputation",
        "validations": { "integer": {} },
        "permissions": {
          "view": ["admin", "user"],
          "edit": ["admin"]
        }
      }
    ]
  }
}
```

---

## 5. PULSAR TOPIC CONFIGURATION

```bash
#!/bin/bash
PULSAR_ADMIN="pulsar-admin"

# Forum content events
echo "Creating forum content topics..."
$PULSAR_ADMIN topics create persistent://public/default/forum.content.created --partitions 12
$PULSAR_ADMIN topics create persistent://public/default/forum.content.updated --partitions 6
$PULSAR_ADMIN topics create persistent://public/default/forum.content.deleted --partitions 3

# User activity events
echo "Creating forum user activity topics..."
$PULSAR_ADMIN topics create persistent://public/default/forum.user.activity --partitions 6
$PULSAR_ADMIN topics create persistent://public/default/forum.user.presence --partitions 6

# Notification events
echo "Creating forum notification topics..."
$PULSAR_ADMIN topics create persistent://public/default/forum.notifications --partitions 6

# Moderation events
echo "Creating forum moderation topics..."
$PULSAR_ADMIN topics create persistent://public/default/forum.moderation.actions --partitions 3

# Analytics events
echo "Creating forum analytics topics..."
$PULSAR_ADMIN topics create persistent://public/default/forum.analytics --partitions 12

# Set retention policies
echo "Setting retention policies..."
$PULSAR_ADMIN topics set-retention persistent://public/default/forum.content.created --size 10G --time 30d
$PULSAR_ADMIN topics set-retention persistent://public/default/forum.notifications --size 5G --time 3d
$PULSAR_ADMIN topics set-retention persistent://public/default/forum.moderation.actions --size 20G --time 90d

# Enable compaction for user presence
$PULSAR_ADMIN topics set-compaction-threshold persistent://public/default/forum.user.presence --threshold 1G

# Create subscriptions for services
echo "Creating subscriptions..."
$PULSAR_ADMIN topics subscribe persistent://public/default/forum.content.created --subscription forum-bff-sub
$PULSAR_ADMIN topics subscribe persistent://public/default/forum.content.created --subscription websocket-sub
$PULSAR_ADMIN topics subscribe persistent://public/default/forum.notifications --subscription notification-service-sub
$PULSAR_ADMIN topics subscribe persistent://public/default/forum.analytics --subscription analytics-sub

echo "Topic setup complete!"
```

---

## 6. ENVIRONMENT VARIABLES TEMPLATE

### Forum Strapi (.env)
```bash
HOST=0.0.0.0
PORT=1338
APP_KEYS=your-app-keys-here
API_TOKEN_SALT=your-api-token-salt
ADMIN_JWT_SECRET=your-admin-jwt-secret
TRANSFER_TOKEN_SALT=your-transfer-token-salt
JWT_SECRET=your-jwt-secret

DATABASE_CLIENT=postgres
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=forum_strapi
DATABASE_USERNAME=forum_user
DATABASE_PASSWORD=your-secure-password
DATABASE_SSL=false

KEYCLOAK_URL=https://auth.venus.com
KEYCLOAK_REALM=venus-platform
KEYCLOAK_CLIENT_ID=venus-forum-client
KEYCLOAK_CLIENT_SECRET=your-keycloak-client-secret

PULSAR_SERVICE_URL=pulsar://localhost:6650
PULSAR_TOKEN=your-pulsar-token

UPLOAD_PROVIDER=local
UPLOAD_MAX_SIZE=10000000
```

### Forum BFF (.env)
```bash
NODE_ENV=production
PORT=4001

FORUM_STRAPI_URL=http://localhost:1338
FORUM_STRAPI_API_TOKEN=your-strapi-api-token

VENUS_BFF_URL=http://localhost:4000

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

PULSAR_SERVICE_URL=pulsar://localhost:6650
PULSAR_TOKEN=your-pulsar-token

KEYCLOAK_URL=https://auth.venus.com
KEYCLOAK_CLIENT_ID=venus-bff-client
KEYCLOAK_CLIENT_SECRET=your-bff-client-secret

RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

DEFAULT_CACHE_TTL=300
FORUM_LIST_CACHE_TTL=300
TOPIC_LIST_CACHE_TTL=120
TOPIC_DETAIL_CACHE_TTL=60
```

### WebSocket Server (.env)
```bash
NODE_ENV=production
PORT=4002

REDIS_URL=redis://localhost:6379

PULSAR_SERVICE_URL=pulsar://localhost:6650
PULSAR_TOKEN=your-pulsar-token

ALLOWED_ORIGINS=https://venus.com,https://www.venus.com
```

### Astro Frontend (.env)
```bash
PUBLIC_BFF_URL=https://api.venus.com
PUBLIC_WS_URL=wss://ws.venus.com
PUBLIC_KEYCLOAK_URL=https://auth.venus.com
PUBLIC_SITE_URL=https://venus.com

BFF_API_TOKEN=your-bff-api-token
```
