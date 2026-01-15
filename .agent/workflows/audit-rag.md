---
description: Optimize RAG system performance
---

# /audit-rag - RAG System Optimization

Audita y optimiza el sistema RAG consultando al subagente especializado.

## Objetivo

Mejorar:
- Precisión de respuestas
- Velocidad de retrieval
- Calidad de embeddings
- Efectividad de prompts

## Pasos

### 1. Consultar RAG Optimizer Agent

Leer `.agent/agents/rag-optimizer.md` para contexto especializado.

### 2. Analizar Configuración Actual

```python
# Revisar app/services/rag_query.py
- Chunk size actual
- Overlap percentage
- Top K (número de documentos recuperados)
- Temperature del modelo
```

### 3. Revisar Métricas

```json
{
  "avg_response_time": "2.3s",
  "avg_relevance_score": 0.78,
  "hallucination_rate": 0.05,
  "user_satisfaction": 0.82
}
```

### 4. Generar Reporte de Optimización

```markdown
## 🧪 RAG Audit Report

### Configuración Actual
- **Chunk Size:** 500 caracteres
- **Overlap:** 10%
- **Top K:** 5 documentos
- **Model:** Gemini 1.5 Flash
- **Temperature:** 0.2

### Métricas
- ⚠️ Tiempo de respuesta: 2.3s (objetivo: <1.5s)
- ✅ Relevancia: 0.78 (bueno)
- ⚠️ Tasa de alucinación: 5% (objetivo: <2%)

### Recomendaciones

#### 1. Reducir Chunk Size (500 → 400)
**Razón:** Chunks más pequeños = búsqueda más precisa
**Impacto:** +10% precisión, -15% tiempo de respuesta
**Riesgo:** Bajo

#### 2. Aumentar Overlap (10% → 20%)
**Razón:** Evitar cortar frases a la mitad
**Impacto:** -30% alucinaciones
**Riesgo:** +10% storage

#### 3. Optimizar System Prompt
**Actual:** "Responde basado en el contexto"
**Sugerido:** "Responde SOLO con información del contexto. Si no sabes, di 'No tengo esa información en los documentos'."
**Impacto:** -50% alucinaciones
```

### 5. Aplicar Cambios (con confirmación)

```python
# app/services/rag_ingest.py
CHUNK_SIZE = 400  # Antes: 500
OVERLAP = 0.20    # Antes: 0.10

# app/services/rag_query.py
SYSTEM_PROMPT = """
Eres un asistente que responde preguntas basándose ÚNICAMENTE en el contexto proporcionado.

Reglas estrictas:
1. Si la respuesta no está en el contexto, di "No tengo esa información"
2. No inventes ni asumas información
3. Cita las fuentes cuando sea posible
4. Usa formato Markdown para claridad
"""
```

### 6. Ejecutar Tests A/B

```python
# Comparar antes/después
test_queries = [
    "¿Cuál es el RUC de la empresa?",
    "Resume el documento",
    "¿Qué dice sobre impuestos?"
]

# Medir:
# - Tiempo de respuesta
# - Precisión (manual review)
# - Satisfacción del usuario
```

## Consulta al Subagente

El RAG Optimizer Agent (`rag-optimizer.md`) tiene conocimiento sobre:
- Estrategias de chunking
- Métricas de similarity (cosine vs euclidean)
- Tuning de temperatura
- Optimización de num_candidates en MongoDB Vector Search

## Resultado Esperado

```
✅ RAG Optimization Complete

Cambios aplicados:
- Chunk size: 500 → 400 chars
- Overlap: 10% → 20%
- System prompt mejorado

Mejoras esperadas:
- -30% tiempo de respuesta
- -50% alucinaciones
- +10% precisión

Próximos pasos:
- Monitorear métricas por 7 días
- Ejecutar A/B test con usuarios
```
