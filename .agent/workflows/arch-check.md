---
description: Validate layered architecture rules
---

# /arch-check - Architecture Validation

Valida que el código siga las reglas de arquitectura por capas definidas en `.agent/CONVENTIONS.md`.

## Objetivo

Detectar violaciones de arquitectura como:
- API importando directamente de Infra (debe usar Service)
- Domain importando librerías externas pesadas
- Circular dependencies
- Imports prohibidos entre capas

## Pasos

### 1. Ejecutar Script de Auditoría
// turbo
```bash
python .agent/audit_arch.py
```

### 2. Analizar Resultados

El script retorna:
- **EXIT 0** - Sin violaciones
- **EXIT 1** - Violaciones encontradas

### 3. Generar Reporte

Si hay violaciones, mostrar:

```
❌ Violaciones de Arquitectura Encontradas:

📁 app/api/v1/projects.py
  ❌ Línea 15: Importa directamente de app.infra.mongo_client
     Solución: Usar app.services.project_service en su lugar

📁 app/domain/user.py
  ⚠️  Línea 8: Importa pymongo (librería externa pesada)
     Solución: Domain debe ser puro, mover lógica a Infra

Total: 2 violaciones críticas, 1 advertencia
```

### 4. Bloquear PR si es Crítico

Si hay violaciones **críticas**, no permitir:
- Crear PR (`/create-pr`)
- Merge a develop
- Deploy a producción

### 5. Sugerir Auto-fixes

Para violaciones comunes, sugerir:

```
💡 Auto-fix disponible:

Violación: API → Infra directo
Fix: Crear método en Service layer

¿Quieres que genere el código automáticamente? (y/n)
```

## Reglas de Arquitectura

### ✅ Permitido
- API → Service
- Service → Infra
- Service → Domain
- Infra → Domain
- Service → Service (con cuidado)

### ❌ Prohibido
- API → Infra (saltar Service)
- API → Domain directo
- Domain → Infra
- Domain → Service
- Infra → API
- Circular dependencies

## Configuración

El script `audit_arch.py` lee las reglas de `.agent/CONVENTIONS.md`.

Para agregar excepciones, editar:
```python
# En audit_arch.py
ALLOWED_EXCEPTIONS = [
    "app/api/health.py",  # Health check puede acceder a Infra
]
```

## Integración con CI/CD

Este workflow se ejecuta automáticamente en:
- Pre-commit hook
- GitHub Actions (PR validation)
- Pre-push hook

## Resultado Esperado

```
✅ Architecture Check: PASSED

Todas las capas respetan las reglas de arquitectura.
0 violaciones encontradas.
```
