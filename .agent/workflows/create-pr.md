---
description: Create GitHub PR with automated validation
---

# /create-pr - GitHub Pull Request Creation

Crea un Pull Request en GitHub con validación completa, descripción automática, y asignación de reviewers.

## Pre-requisitos

1. **GitHub CLI instalado** - `gh` debe estar disponible
2. **Autenticado** - `gh auth status` debe mostrar autenticación válida
3. **Commits en la rama** - Debe haber al menos 1 commit
4. **No estar en develop/main** - Debe ser una feature/bugfix/hotfix branch

## Pasos

### 1. Validar Pre-requisitos

```bash
# Verificar rama actual
git branch --show-current
```
**Bloquear si:** Estamos en `develop` o `main`

```bash
# Verificar que hay commits
git log origin/develop..HEAD --oneline
```
**Bloquear si:** No hay commits nuevos

### 2. Ejecutar Validaciones Pre-PR

#### a) Architecture Check
```bash
python .agent/audit_arch.py
```
**Bloquear si:** Hay violaciones críticas de arquitectura

#### b) Linting
```bash
ruff check app/
```
**Advertir si:** Hay errores de linting (pero no bloquear)

#### c) Tests (si existen)
```bash
pytest tests/ -v
```
**Bloquear si:** Tests fallan

### 3. Analizar Cambios

```bash
# Obtener archivos modificados
git diff --name-status origin/develop...HEAD

# Obtener estadísticas
git diff --stat origin/develop...HEAD
```

### 4. Generar Descripción Automática

**Analizar commits:**
```bash
git log origin/develop..HEAD --pretty=format:"%s"
```

**Template de descripción:**
```markdown
## 🎯 Objetivo
[Descripción generada basada en commits y archivos modificados]

## 📝 Cambios Principales

### Archivos Modificados
- `app/services/NOMBRE.py` - [Descripción del cambio]
- `app/api/v1/NOMBRE.py` - [Descripción del cambio]

### Estadísticas
- X archivos modificados
- +Y inserciones, -Z eliminaciones

## ✅ Checklist de Validación

- [x] Arquitectura validada (`/arch-check`)
- [x] Código linteado (`/lint`)
- [x] Tests pasando
- [ ] Documentación actualizada (si aplica)
- [x] Sin imports dentro de funciones
- [ ] Reviewed by: [Auto-asignado según CODEOWNERS]

## 🔗 Issues Relacionados
[Si hay referencias a issues en commits, listarlos aquí]

## 🧪 Cómo Probar
[Instrucciones generadas basadas en los cambios]

---
🤖 PR auto-generado por Antigravity
```

### 5. Determinar Labels

Basado en el nombre de la rama:
- `feature/*` → label: `feature`, `enhancement`
- `bugfix/*` → label: `bug`, `fix`
- `hotfix/*` → label: `hotfix`, `critical`
- `refactor/*` → label: `refactor`, `tech-debt`

### 6. Push a Remote

```bash
git push origin HEAD
```

### 7. Crear PR con GitHub CLI

```bash
gh pr create \
  --title "[AUTO] TITULO_GENERADO" \
  --body "DESCRIPCION_GENERADA" \
  --base develop \
  --label "LABELS_DETERMINADOS" \
  --assignee @me
```

### 8. Auto-asignar Reviewers

Leer `.github/CODEOWNERS` (si existe) y asignar reviewers según los archivos modificados.

```bash
# Si CODEOWNERS especifica reviewers para los archivos modificados
gh pr edit --add-reviewer REVIEWER_USERNAME
```

### 9. Agregar Comentario con Validaciones

```bash
gh pr comment --body "## ✅ Validaciones Automáticas

- ✅ Architecture check: PASSED
- ✅ Linting: PASSED  
- ✅ Tests: PASSED

Listo para review humano 🚀"
```

## Resultado Esperado

- ✅ PR creado en GitHub
- ✅ Descripción completa y profesional
- ✅ Labels aplicados correctamente
- ✅ Reviewers asignados (si hay CODEOWNERS)
- ✅ Todas las validaciones ejecutadas
- ✅ Comentario con status de validaciones

## Manejo de Errores

### Si las validaciones fallan:
```
❌ No se puede crear el PR. Errores encontrados:

- Architecture: 3 violaciones críticas
- Tests: 2 tests fallando

Por favor, corrige estos errores y vuelve a ejecutar /create-pr
```

### Si GitHub CLI no está instalado:
```
⚠️ GitHub CLI no encontrado.

Opciones:
1. Instalar: https://cli.github.com/
2. Crear PR manualmente en GitHub
3. Usar API de GitHub (requiere token)
```

## Notas

- El PR siempre se crea contra `develop` (no `main`)
- Para hotfixes, el workflow `/hotfix` maneja el merge a `main`
- La descripción se puede editar manualmente después de crear el PR
