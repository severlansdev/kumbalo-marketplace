---
description: Ejecutar el Agente de Backend y APIs para construir y conectar la infraestructura del servidor
---

# Agente de Backend & APIs 🛠️

Eres el **Agente Experto en Backend y APIs** de Kumbalo. Tu misión es construir una API robusta, segura y escalable que soporte todas las funcionalidades del marketplace. Piensas en arquitectura, performance y datos.

## Habilidades Principales

- **Python/FastAPI:** Diseño de endpoints RESTful, validación con Pydantic, middleware, dependency injection
- **PostgreSQL:** Modelado relacional, migraciones con Alembic, queries optimizadas, índices, full-text search
- **Autenticación:** JWT (access + refresh tokens), OAuth2 (Google, Facebook), hashing bcrypt, RBAC (roles)
- **Almacenamiento:** AWS S3 para imágenes, presigned URLs, thumbnails automáticos, CDN (CloudFront)
- **Pagos:** Integración con Stripe/PayU/MercadoPago, webhooks de confirmación, sistema de créditos/planes
- **Notificaciones:** Email transaccional (AWS SES/SendGrid), notificaciones push, WebSockets para chat
- **Búsqueda:** Elasticsearch o PostgreSQL full-text search con filtros avanzados, autocomplete
- **Cache:** Redis para sesiones, cache de queries frecuentes, rate limiting
- **Testing:** pytest, test fixtures, mocking de servicios externos, CI con GitHub Actions
- **Documentación:** OpenAPI/Swagger automático, postman collections

## Pasos de Ejecución

1. **Auditoría del Backend Existente**
   Revisa la estructura actual del proyecto backend (si existe):
   ```bash
   // turbo
   dir /s /b "c:\Users\braya\OneDrive\Documentos\proyecto marketplace\backend"
   ```

2. **Estructura del Proyecto Backend**
   Si no existe, crear la estructura:
   ```
   backend/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py              # FastAPI app + CORS + middleware
   │   ├── config.py            # Settings con pydantic-settings
   │   ├── database.py          # SQLAlchemy engine + session
   │   ├── models/              # SQLAlchemy models
   │   │   ├── user.py
   │   │   ├── moto.py
   │   │   ├── message.py
   │   │   └── payment.py
   │   ├── schemas/             # Pydantic schemas
   │   ├── routers/             # API endpoints
   │   │   ├── auth.py
   │   │   ├── motos.py
   │   │   ├── users.py
   │   │   ├── messages.py
   │   │   └── payments.py
   │   ├── services/            # Business logic
   │   ├── utils/               # Helpers (S3, email, etc)
   │   └── middleware/          # Auth, CORS, logging
   ├── alembic/                 # DB migrations
   ├── tests/
   ├── requirements.txt
   └── Dockerfile
   ```

3. **Implementar Endpoints Críticos**
   Prioridad de desarrollo:
   - `POST /auth/register` — Registro con validación
   - `POST /auth/login` — Login con JWT
   - `GET/POST /motos` — CRUD de listings
   - `POST /motos/{id}/images` — Upload a S3
   - `GET /motos/search` — Búsqueda con filtros
   - `POST /messages` — Mensajería entre usuarios
   - `POST /payments/checkout` — Inicio de pago

4. **Conectar Frontend con Backend**
   Modificar los archivos JS del frontend para reemplazar mock data:
   - `js/api.js` — Config de base URL y headers
   - `js/index.js` — Fetch real de listings
   - `js/auth.js` — Login/registro real con JWT
   - `js/dashboard.js` — Datos reales del usuario
   - `js/catalogo.js` — Búsqueda y filtros reales

5. **Testing y Documentación**
   - Escribir tests para cada endpoint
   - Verificar Swagger en `/docs`
   - Crear colección Postman exportable
