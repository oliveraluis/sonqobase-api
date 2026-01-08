# 🏗️ SonqoBase Architecture & Conventions

Este documento define la **Verdad Única** sobre cómo se escribe código en este proyecto. Cualquier desviación debe ser justificada.

## 1. Patrón de Arquitectura (Layered/Clean-ish)
El proyecto sigue una arquitectura por capas estricta para garantizar mantenibilidad y testabilidad.

### 🏛️ Las Capas (De afuera hacia adentro)

1.  **API Layer (`app/api/`)** 🛂
    *   **Responsabilidad:** Recibir HTTP requests, validar DTOs (Pydantic), llamar al Servicio.
    *   **Prohibido:** Lógica de negocio, consultas directas a DB (`pymongo`), instanciar repositorios directamente (usar inyección/fábricas).
    *   **Retorno:** Siempre retorna Pydantic Models o `JSONResponse`.

2.  **Service Layer (`app/services/`)** 🧠
    *   **Responsabilidad:** Orquestar la lógica de negocio (Use Cases). Es el "corazón" del sistema.
    *   **Input:** Tipos nativos o DTOs.
    *   **Dependencias:** Repositorios (`app/infra`), Event Bus, otros Servicios.
    *   **Regla de Oro:** Un servicio ejecuta UNA cosa (Single Responsibility). Ej: `CreateUserService`, `RagQueryService`.

3.  **Domain Layer (`app/domain/`)** 💎
    *   **Responsabilidad:** Entidades puras, Value Objects, Eventos de Dominio.
    *   **Prohibido:** Importar `app/infra` o librerías externas pesadas. Debe ser puro Python.

4.  **Infrastructure Layer (`app/infra/`)** 🔌
    *   **Responsabilidad:** Implementación técnica. Repositorios de MongoDB, Clientes HTTP, Adaptadores de AI (Gemini).
    *   **Regla:** Aquí y SOLO aquí se toca `pymongo` o APIs externas.

5.  **Listeners (`app/listeners/`)** 👂
    *   **Responsabilidad:** Manejar efectos secundarios asíncronos (Audit, Email, Embeddings).
    *   **Trigger:** Eventos del `EventBus` (`app/infra/event_bus.py`).

## 2. Stack Tecnológico & Librerías

*   **Framework:** FastAPI (Async por defecto).
*   **DB:** MongoDB (usando `pymongo` oficial).
    *   *Nota:* No usamos ODMs complejos (como Beanie) para mantener control total de las queries y performance.
*   **AI:** Google Gemini 1.5 Flash (vía SDK oficial o REST).
*   **Auth:** API Keys Custom (User Key `sonqo_user_` / Project Key `sonqo_proj_`).

## 3. Reglas de Código (Style Guide)

*   **Typing:** OBLIGATORIO en firmas de funciones. `def fn(a: str) -> int:`.
*   **Docstrings:** Todo módulo y función pública debe tener docstring.
*   **Async:** Preferir `async/await` para I/O bound (DB, HTTP).
*   **Config:** Variables de entorno vía `app/config.py` (Pydantic Settings). NO `os.getenv` dispersos.

## 4. Flujo de Trabajo para Nuevas Features

1.  Definir la Entidad/Modelo en `app/domain` o DTO en `app/models`.
2.  Crear el Repositorio en `app/infra` (si hay persistencia).
3.  Crear el Servicio en `app/services` (Lógica).
4.  Crear el Endpoint en `app/api/v1` (Expo).
5.  Registrar el router en `app/main.py`.
