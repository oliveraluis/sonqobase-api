# 🎨 SonqoBase Code Style Guide

Este documento define las reglas de estilo de código para SonqoBase. Todos los contribuidores (humanos y AI) deben seguir estas convenciones.

## 🚨 Reglas Críticas (No Negociables)

### 1. Imports SIEMPRE en la Raíz del Archivo

❌ **INCORRECTO:**
```python
def my_function():
    import requests  # Import dentro de función
    return requests.get("https://api.example.com")

class MyClass:
    def method(self):
        from app.services import something  # Import dentro de clase
        return something()
```

✅ **CORRECTO:**
```python
import requests
from app.services import something

def my_function():
    return requests.get("https://api.example.com")

class MyClass:
    def method(self):
        return something()
```

**Razón:** 
- Claridad: Se ve inmediatamente qué dependencias tiene el archivo
- Performance: Imports se ejecutan una vez, no en cada llamada
- Linting: Herramientas pueden detectar imports no usados

**Excepciones:** NINGUNA (salvo casos extremos de circular imports, que deben refactorizarse)

### 2. Orden de Imports (PEP 8)

```python
# 1. Standard library
import os
import sys
from typing import Optional, Dict, Any

# 2. Third-party libraries
import pymongo
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# 3. Local imports (app)
from app.config import settings
from app.domain.user import User
from app.infra.mongo_client import get_mongo_client
```

**Herramienta:** `isort` automatiza esto

### 3. Type Hints Obligatorios

❌ **INCORRECTO:**
```python
def create_user(name, email):
    return {"name": name, "email": email}
```

✅ **CORRECTO:**
```python
def create_user(name: str, email: str) -> Dict[str, str]:
    return {"name": name, "email": email}
```

**Razón:**
- Autocomplete en IDE
- Detección temprana de errores
- Documentación implícita

### 4. Docstrings en Funciones Públicas

✅ **CORRECTO:**
```python
def create_project(user_id: str, name: str) -> Dict[str, Any]:
    """
    Create a new project for a user.
    
    Args:
        user_id: Unique identifier of the user
        name: Name of the project
        
    Returns:
        Dictionary with project data including project_id
        
    Raises:
        ValueError: If name is empty
        UserNotFoundError: If user_id doesn't exist
    """
    if not name:
        raise ValueError("Project name cannot be empty")
    # Implementation...
```

**Formato:** Google Style (usado por Gemini)

## 📏 Formateo

### Line Length
- **Máximo:** 100 caracteres
- **Recomendado:** 80-90 caracteres

### Indentación
- **Espacios:** 4 (no tabs)
- **Continuación de línea:** 4 espacios adicionales

```python
# ✅ CORRECTO
result = some_function(
    argument1,
    argument2,
    argument3
)

# ❌ INCORRECTO (2 espacios)
result = some_function(
  argument1,
  argument2
)
```

### Blank Lines
- **2 líneas** entre funciones de nivel superior
- **2 líneas** entre clases
- **1 línea** entre métodos de una clase

```python
import os


def function_one():
    pass


def function_two():
    pass


class MyClass:
    def method_one(self):
        pass
    
    def method_two(self):
        pass
```

## 🏗️ Arquitectura de Imports

### Respetar Capas

❌ **PROHIBIDO:**
```python
# En app/api/v1/projects.py
from app.infra.mongo_client import get_mongo_client  # API → Infra directo

# En app/domain/user.py
import pymongo  # Domain → Librería externa pesada
```

✅ **CORRECTO:**
```python
# En app/api/v1/projects.py
from app.services.project_service import ProjectService  # API → Service

# En app/domain/user.py
from typing import Optional  # Domain → Solo stdlib
```

## 🔤 Naming Conventions

### Variables y Funciones
- **snake_case**
- Descriptivos, no abreviaciones

```python
# ✅ CORRECTO
user_id = "123"
project_name = "My Project"

def get_user_by_id(user_id: str) -> User:
    pass

# ❌ INCORRECTO
uid = "123"  # Muy corto
pn = "My Project"  # Abreviación

def getUser(id):  # camelCase (no Python)
    pass
```

### Clases
- **PascalCase**
- Sustantivos

```python
# ✅ CORRECTO
class UserService:
    pass

class ProjectRepository:
    pass

# ❌ INCORRECTO
class user_service:  # snake_case
    pass

class GetProject:  # Verbo (debería ser sustantivo)
    pass
```

### Constantes
- **UPPER_SNAKE_CASE**

```python
# ✅ CORRECTO
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
API_VERSION = "v1"
```

### Archivos
- **snake_case.py**

```
✅ CORRECTO:
app/services/rag_query.py
app/infra/gemini_client.py

❌ INCORRECTO:
app/services/RagQuery.py
app/infra/geminiClient.py
```

## 🔄 Async/Sync

### Preferir Async para I/O

```python
# ✅ CORRECTO (I/O bound)
async def get_user(user_id: str) -> User:
    user_data = await db.users.find_one({"_id": user_id})
    return User(**user_data)

# ✅ CORRECTO (CPU bound)
def calculate_embeddings(text: str) -> List[float]:
    # Operación CPU-intensiva, no necesita async
    return model.encode(text)
```

### No Mezclar Sync en Async

❌ **INCORRECTO:**
```python
async def my_async_function():
    result = sync_blocking_call()  # Bloquea el event loop
    return result
```

✅ **CORRECTO:**
```python
import asyncio

async def my_async_function():
    result = await asyncio.to_thread(sync_blocking_call)
    return result
```

## 🛡️ Error Handling

### Específico, no Genérico

❌ **INCORRECTO:**
```python
try:
    user = get_user(user_id)
except Exception:  # Muy genérico
    pass
```

✅ **CORRECTO:**
```python
try:
    user = get_user(user_id)
except UserNotFoundError:
    logger.warning(f"User {user_id} not found")
    raise
except DatabaseConnectionError as e:
    logger.error(f"DB connection failed: {e}")
    raise
```

### Custom Exceptions

```python
# app/domain/exceptions.py
class SonqoBaseException(Exception):
    """Base exception for SonqoBase."""
    pass

class UserNotFoundError(SonqoBaseException):
    """Raised when user is not found."""
    pass

class ProjectQuotaExceededError(SonqoBaseException):
    """Raised when user exceeds project quota."""
    pass
```

## 📝 Comments

### Cuándo Comentar

✅ **CORRECTO:**
```python
# Calculate TTL based on project tier
# Free tier: 7 days, Pro tier: 30 days
ttl_days = 7 if project.tier == "free" else 30
```

❌ **INCORRECTO:**
```python
# Increment counter
counter += 1  # Obvio, no agregar valor
```

### Regla de Oro
- **Código dice QUÉ**
- **Comentarios dicen POR QUÉ**

## 🧪 Testing

### Naming
```python
def test_create_user_with_valid_data():
    """Should create user successfully with valid input."""
    pass

def test_create_user_with_empty_email_raises_error():
    """Should raise ValueError when email is empty."""
    pass
```

### Arrange-Act-Assert
```python
def test_example():
    # Arrange
    user_id = "123"
    expected_name = "John"
    
    # Act
    user = get_user(user_id)
    
    # Assert
    assert user.name == expected_name
```

## 🔧 Herramientas

### Linter: Ruff
```bash
ruff check app/
ruff check app/ --fix  # Auto-fix
```

### Formatter: Black
```bash
black app/
black app/ --check  # Solo verificar
```

### Type Checker: MyPy
```bash
mypy app/ --ignore-missing-imports
```

### Import Sorter: isort
```bash
isort app/
```

## ✅ Checklist Pre-Commit

Antes de hacer commit, verificar:

- [ ] Imports en la raíz del archivo
- [ ] Imports ordenados (stdlib → third-party → local)
- [ ] Type hints en todas las funciones públicas
- [ ] Docstrings en funciones públicas
- [ ] No hay líneas >100 caracteres
- [ ] No hay imports no usados
- [ ] Tests pasan
- [ ] Linter pasa (ruff)

## 🤖 Auto-fixes

El workflow `/lint` puede auto-fixar:
- ✅ Orden de imports
- ✅ Formateo (black)
- ✅ Trailing whitespace
- ⚠️ Mover imports a raíz (con confirmación)

## 📚 Referencias

- [PEP 8](https://peps.python.org/pep-0008/) - Style Guide for Python Code
- [PEP 257](https://peps.python.org/pep-0257/) - Docstring Conventions
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
