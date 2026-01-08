# 🧠 SonqoBase - AI Context & Operations

Este archivo configura el contexto para el desarrollo asistido por IA en SonqoBase.

## 📍 Contexto del Proyecto
*   **Nombre:** SonqoBase API
*   **Misión:** Base de Datos Vectorial Efímera as-a-Service (RAG fácil).
*   **Arquitectura:** Layered (API -> Service -> Infra). Ver `.agent/CONVENTIONS.md`.
*   **Estado:** Producción (MVP).

## 🛠️ Comandos Slash (Workflows)

Usa estos comandos para iniciar flujos de trabajo estandarizados:

*   `/arch-check` -> Verifica que no se violen las reglas de capas (imports prohibidos).
*   `/new-feature` -> Inicia el scaffold de una nueva funcionalidad siguiendo las capas.
*   `/audit-rag` -> Revisa el flujo de RAG query y optimización.
*   `/docs` -> Actualiza `docs.html` basado en cambios recientes en la API.

## 🚨 Reglas de Comportamiento (System Prompts)

1.  **Strict Layering:** Si el usuario pide un endpoint, NUNCA escribas lógica en el controlador. Crea un `Service`.
2.  **No Hallucinations:** Si no conoces una librería, usa la estándar (`pymongo`, `requests`, `httpx`).
3.  **Security First:** Siempre valida ownership de recursos (`user_id` en queries).
4.  **Performance:** Cuidado con `Sync` en rutas `Async`.

## 📂 Mapa Mental (File Structure)

*   `app/api/` -> Rutas / Controladores
*   `app/services/` -> Lógica de Negocio (Use Cases)
*   `app/infra/` -> DB, AI Clients, Event Bus
*   `app/domain/` -> Modelos puros
*   `app/listeners/` -> Event Handlers
*   `app/templates/` -> Frontend (Jinja2)
*   `app/static/` -> CSS/JS

## 🔄 Rutinas Comunes

### Iniciar nueva Feature
1. Revisa `.agent/CONVENTIONS.md`.
2. Define los modelos de datos.
3. Implementa de adentro hacia afuera: Infra -> Service -> API.
