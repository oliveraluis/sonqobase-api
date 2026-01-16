# 🎓 Lecciones Aprendidas - Cost Monitoring Implementation

## Error Común: Violación de Arquitectura por Capas

### ❌ Lo que NO se debe hacer:
```python
# En Service accediendo directamente a MongoDB
class CostMonitoringService:
    def __init__(self):
        self.db = get_mongo_client()  # ❌ Service accediendo a DB directamente
        self.collection = self.db.cost_metrics
```

### ✅ Lo CORRECTO (Arquitectura por Capas):
```python
# API → Service → Repository → MongoDB

# Repository (Infra Layer)
class CostMetricsRepository:
    def insert_usage(self, metric: Dict[str, Any]) -> None:
        client = get_mongo_client()
        db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        db.cost_metrics.insert_one(metric)

# Service (Business Logic Layer)
class CostMonitoringService:
    def __init__(self, repository: CostMetricsRepository = None):
        self.repository = repository or CostMetricsRepository()
    
    def log_gemini_usage(self, ...):
        # Business logic (calculate costs)
        metric = {...}
        # Delegate to repository
        self.repository.insert_usage(metric)
```

## Patrón Correcto de Repository

### Basado en `UserRepository`:
1. **Cada método obtiene client y db**
2. **No guardar state en __init__**
3. **Seguir el mismo patrón en todos los repos**

```python
def method_name(self, ...):
    client = get_mongo_client()
    db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
    db = client[db_name]
    
    # Operación en DB
    return db.collection.find(...)
```

## Async vs Sync

### ❌ Error: Mezclar async/sync incorrectamente
```python
async def create_indexes(self) -> None:
    await self.collection.create_index(...)  # ❌ create_index no es async
```

### ✅ Correcto: pymongo es sync, no async
```python
def create_indexes(self) -> None:
    self.collection.create_index(...)  # ✅ Sync
```

**Nota:** Si necesitas async, usa `motor` (motor.motor_asyncio), no `pymongo`.

## Regla de Oro

**SIEMPRE revisar repositorios existentes antes de crear uno nuevo:**
1. Ver `user_repository.py`
2. Ver `project_repository.py`
3. Seguir el MISMO patrón
4. No inventar nuevos patrones

## Documentar en Agentes

Agregar a `.agent/CONVENTIONS.md`:

```markdown
### Repository Pattern
- Cada método obtiene `client` y `db` (no guardar en __init__)
- Usar `get_mongo_client()` y extraer db_name de settings
- pymongo es SYNC, no async
- Seguir patrón de `UserRepository`
```

---

**Fecha:** 2026-01-15
**Contexto:** Implementación de cost monitoring
**Aprendizaje:** Respetar arquitectura por capas es CRÍTICO
