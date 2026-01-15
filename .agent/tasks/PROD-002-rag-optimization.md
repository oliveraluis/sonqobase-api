# 🧪 RAG Optimization - Token Reduction Strategy

## Objective
Reduce Gemini token usage by 30% through optimization of chunk size, overlap, prompts, and caching.

**Consulting:** `.agent/agents/rag-optimizer.md`

## Current Configuration Analysis

### Check Current Settings
**File:** `app/services/rag_ingest.py`

```python
# Current settings (to verify)
CHUNK_SIZE = ???  # Check actual value
OVERLAP = ???     # Check actual percentage
```

**File:** `app/services/rag_query.py`

```python
# Current settings
TOP_K = ???              # Number of chunks retrieved
SYSTEM_PROMPT = ???      # Current prompt
TEMPERATURE = ???        # Model temperature
```

---

## Optimization Strategy

### 1. Optimize Chunk Size (Target: -15% tokens)

**Current Issue:** Chunks too large = more tokens per query

**Recommendation from RAG Optimizer Agent:**
- **Current:** Likely 500-800 chars
- **Optimized:** 350-450 chars
- **Rationale:** Smaller chunks = more precise retrieval = fewer irrelevant tokens

**Implementation:**
```python
# app/services/rag_ingest.py

# Before
CHUNK_SIZE = 500  # or whatever current value is

# After
CHUNK_SIZE = 400  # Optimized for precision
```

**Expected Impact:**
- Input tokens: -20% (smaller chunks)
- Output tokens: -10% (more focused responses)
- **Total reduction:** ~15%

---

### 2. Increase Overlap (Target: Better quality, same tokens)

**Current Issue:** Chunks cut sentences = context loss = more queries

**Recommendation:**
- **Current:** Likely 10% or less
- **Optimized:** 20%
- **Rationale:** Prevents cutting sentences mid-way

**Implementation:**
```python
# app/services/rag_ingest.py

# Before
OVERLAP_PERCENTAGE = 0.10

# After
OVERLAP_PERCENTAGE = 0.20  # Better context preservation
```

**Expected Impact:**
- Slightly more storage (+10%)
- Better retrieval quality
- Fewer follow-up queries needed
- **Net effect:** Neutral on tokens, better UX

---

### 3. Optimize System Prompt (Target: -10% output tokens)

**Current Issue:** Verbose prompts = more output tokens

**Current Prompt (likely):**
```
"You are a helpful assistant. Answer the question based on the context provided."
```

**Optimized Prompt:**
```python
# app/services/rag_query.py

SYSTEM_PROMPT = """Responde SOLO con información del contexto proporcionado.

Reglas:
1. Si la respuesta no está en el contexto, di "No tengo esa información"
2. Sé conciso y directo
3. No inventes ni asumas información
4. Usa formato Markdown solo si mejora claridad

Contexto:
{context}

Pregunta: {query}"""
```

**Key Changes:**
- ✅ Explicit instruction to be concise
- ✅ Clear fallback ("No tengo esa información")
- ✅ Markdown only when needed (saves tokens)

**Expected Impact:**
- Output tokens: -10%
- Hallucination rate: -50%

---

### 4. Reduce Top K (Target: -10% input tokens)

**Current Issue:** Retrieving too many chunks = wasted tokens

**Analysis:**
```python
# Test different Top K values
TOP_K_OPTIONS = [3, 5, 7, 10]

# For most queries, Top K = 5 is sufficient
# Specific queries (like "What's the RUC?") only need Top K = 3
```

**Implementation:**
```python
# app/services/rag_query.py

# Dynamic Top K based on query type
def determine_top_k(query: str) -> int:
    """Determine optimal Top K based on query."""
    # Specific fact queries
    if any(word in query.lower() for word in ["qué es", "cuál es", "ruc", "fecha"]):
        return 3
    
    # Summary queries
    if any(word in query.lower() for word in ["resume", "explica", "describe"]):
        return 10
    
    # Default
    return 5

# Use in query
top_k = determine_top_k(user_query)
results = await vector_search(query_embedding, top_k=top_k)
```

**Expected Impact:**
- Input tokens: -10% (fewer chunks)
- Precision: Same or better (dynamic selection)

---

### 5. Implement Response Caching (Target: -40% on repeated queries)

**Strategy:** Cache common queries to avoid Gemini calls

**Implementation:**
```python
# app/services/rag_query.py
from functools import lru_cache
import hashlib

class RAGQueryService:
    def __init__(self):
        self.cache = {}  # Simple in-memory cache
        # TODO: Use Redis for production
    
    def get_cache_key(self, query: str, project_id: str) -> str:
        """Generate cache key for query."""
        content = f"{project_id}:{query}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def query_with_cache(
        self,
        query: str,
        project_id: str,
        ttl_seconds: int = 3600  # 1 hour
    ):
        """Query with caching."""
        cache_key = self.get_cache_key(query, project_id)
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.utcnow() - cached["timestamp"]).seconds < ttl_seconds:
                return {
                    **cached["response"],
                    "cached": True
                }
        
        # Not in cache, query Gemini
        response = await self.query_gemini(query, project_id)
        
        # Store in cache
        self.cache[cache_key] = {
            "response": response,
            "timestamp": datetime.utcnow()
        }
        
        return {
            **response,
            "cached": False
        }
```

**Expected Impact:**
- 30-40% of queries are repeated
- **Token reduction:** ~40% on cached queries
- **Cost reduction:** ~40% on cached queries

---

### 6. Optimize Temperature (Target: -5% output tokens)

**Current:** Likely 0.7 (default)
**Optimized:** 0.2

**Rationale:**
- Lower temperature = more deterministic = shorter responses
- For RAG, we want facts, not creativity

**Implementation:**
```python
# app/services/rag_query.py

# Before
temperature = 0.7

# After
temperature = 0.2  # Fact-based, concise responses
```

**Expected Impact:**
- Output tokens: -5%
- Response consistency: +50%

---

## Implementation Plan

### Phase 1: Quick Wins (1-2 hours)
1. ✅ Reduce chunk size (500 → 400)
2. ✅ Increase overlap (10% → 20%)
3. ✅ Optimize system prompt
4. ✅ Lower temperature (0.7 → 0.2)

**Expected reduction:** ~20%

---

### Phase 2: Dynamic Optimization (2-3 hours)
1. ✅ Implement dynamic Top K
2. ✅ Add response caching (in-memory)

**Expected reduction:** ~30% (with cache hits)

---

### Phase 3: Advanced (Future)
1. Redis caching (production-ready)
2. Semantic deduplication of chunks
3. Query rewriting for efficiency

**Expected reduction:** ~40-50%

---

## Testing & Validation

### Before Optimization
```python
# Measure baseline
test_queries = [
    "¿Cuál es el RUC de la empresa?",
    "Resume el documento",
    "¿Qué dice sobre impuestos?"
]

for query in test_queries:
    response = await rag_service.query(query, project_id)
    print(f"Query: {query}")
    print(f"Input tokens: {response['input_tokens']}")
    print(f"Output tokens: {response['output_tokens']}")
    print(f"Total cost: ${response['cost']:.4f}")
```

### After Optimization
Run same queries and compare:
- Input tokens reduction
- Output tokens reduction
- Cost reduction
- Response quality (manual review)

---

## Expected Results

### Token Reduction
```
Before:
- Avg input tokens: 2000
- Avg output tokens: 500
- Total: 2500 tokens/query

After:
- Avg input tokens: 1400 (-30%)
- Avg output tokens: 400 (-20%)
- Total: 1800 tokens/query (-28%)
```

### Cost Reduction
```
Before: $0.001 per query
After: $0.0007 per query (-30%)

At 50k queries/month:
- Before: $50/month
- After: $35/month
- Savings: $15/month (30%)
```

---

## Monitoring

After implementing, monitor:
1. **Token usage** (via PROD-001 monitoring)
2. **Response quality** (user feedback, NPS)
3. **Cache hit rate** (target: >30%)
4. **Latency** (should stay <2s)

---

## Rollback Plan

If quality degrades:
1. Revert chunk size to 500
2. Revert Top K to 5 (static)
3. Keep prompt optimization (no downside)
4. Keep caching (no downside)

---

**Estimated Time:** 3-5 hours
**Priority:** High (PROD-002)
**Owner:** RAG Optimizer Agent + CTO
