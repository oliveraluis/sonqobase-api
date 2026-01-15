# 💰 SonqoBase - Infrastructure & Cost Analysis

## Current Infrastructure (MVP - Beta)

### Hosting & Deployment
- **Platform:** Render (Free Tier)
- **Cost:** $0/mes
- **Limitations:**
  - Sleep after 15 min de inactividad
  - 512 MB RAM
  - Shared CPU
  - 100 GB bandwidth/mes

### Database
- **Platform:** MongoDB Atlas (Free Tier - M0)
- **Cost:** $0/mes
- **Limitations:**
  - 512 MB storage
  - Shared cluster
  - No backups automáticos
  - Conexiones limitadas

### AI Model
- **Platform:** Google Gemini 1.5 Flash
- **Tier:** Pay-as-you-go (versión pagada básica)
- **Pricing:**
  - Input: $0.075 per 1M tokens
  - Output: $0.30 per 1M tokens
- **Current Usage:** Bajo (beta con 1 cliente)
- **Estimated Cost:** $0-5/mes en beta

### Development Tools
- **Antigravity (Claude Sonnet 4):** Google One Plan
- **Cost:** ~8 PEN por 3 meses (personal)
- **Note:** Gasto individual del founder, no del proyecto

---

## Cost Breakdown (Current)

### Monthly Recurring Costs (Proyecto)
```
Render (Free Tier):           $0
MongoDB Atlas (Free Tier):    $0
Gemini API (pay-as-you-go):   $0-5 (bajo uso beta)
─────────────────────────────────
TOTAL MRR (Proyecto):         $0-5
```

### Personal Costs (Founder)
```
Antigravity/Claude:           ~2.67 PEN/mes (~$0.70 USD)
Google One (3 meses):         ~8 PEN total (~$2.10 USD)
```

**Burn Rate Proyecto:** ~$0-5/mes
**Burn Rate Personal:** ~$0.70/mes
**Runway:** Indefinido (free tiers + pay-as-you-go)

---

## Scaling Projections

### Scenario 1: 100 Usuarios Activos
**Assumptions:**
- 10 proyectos activos/usuario
- 50 queries/proyecto/mes
- Promedio 1000 tokens/query

**Costs:**
- **Render:** $7/mes (Starter plan - 512 MB)
- **MongoDB:** $0 (aún en free tier si <512 MB)
- **Gemini:**
  - 100 users × 10 projects × 50 queries = 50k queries/mes
  - 50k × 1000 tokens = 50M tokens
  - Input: 50M × $0.075/1M = $3.75
  - Output: 50M × $0.30/1M = $15
  - **Total Gemini:** ~$19/mes

**Total:** ~$26/mes

---

### Scenario 2: 500 Usuarios Activos (Product-Market Fit)
**Assumptions:**
- 5 proyectos activos/usuario (más realista)
- 100 queries/proyecto/mes
- Promedio 1500 tokens/query

**Costs:**
- **Render:** $25/mes (Standard plan - 2 GB RAM)
- **MongoDB:** $57/mes (M10 cluster - 10 GB)
- **Gemini:**
  - 500 × 5 × 100 = 250k queries/mes
  - 250k × 1500 = 375M tokens
  - Input: 375M × $0.075/1M = $28.13
  - Output: 375M × $0.30/1M = $112.50
  - **Total Gemini:** ~$141/mes

**Total:** ~$223/mes

**Revenue Needed (20% margin):** $278/mes
**Users Needed (at $10/user/mes):** 28 paying users (5.6% conversion)

---

### Scenario 3: 1000+ Usuarios (Scale)
**Assumptions:**
- 3 proyectos activos/usuario
- 150 queries/proyecto/mes
- Promedio 2000 tokens/query

**Costs:**
- **Render:** $85/mes (Pro plan - 4 GB) o migrar a AWS
- **MongoDB:** $180/mes (M30 cluster - 40 GB + backups)
- **Gemini:**
  - 1000 × 3 × 150 = 450k queries/mes
  - 450k × 2000 = 900M tokens
  - Input: 900M × $0.075/1M = $67.50
  - Output: 900M × $0.30/1M = $270
  - **Total Gemini:** ~$338/mes

**Total:** ~$603/mes

**Revenue Needed (30% margin):** $861/mes
**Users Needed (at $15/user/mes):** 58 paying users (5.8% conversion)

---

## Cost Optimization Strategies

### Short-term (MVP → 100 users)
1. **Mantener Free Tiers**
   - Render Free Tier suficiente para beta
   - MongoDB M0 suficiente hasta ~100 proyectos

2. **Optimizar Gemini Usage**
   - Cachear respuestas frecuentes
   - Reducir tokens con mejor chunking
   - Usar temperature baja (menos tokens output)

3. **Monitorear Límites**
   - Alert cuando MongoDB llegue a 400 MB (80% capacity)
   - Alert cuando Render bandwidth > 80 GB

### Medium-term (100 → 500 users)

1. **Tier-based Gemini**
   - Free tier: Gemini Flash (actual)
   - Pro tier: Gemini Pro (mejor calidad)
   - Pasar costos a usuarios premium

2. **Database Optimization**
   - Implementar TTL agresivo en free tier
   - Comprimir embeddings
   - Índices optimizados

3. **Caching Layer**
   - Redis para queries frecuentes
   - Reduce llamadas a Gemini en 30-40%

### Long-term (500+ users)

1. **Infrastructure Migration**
   - Render → AWS/GCP (mejor pricing a escala)
   - Considerar self-hosted MongoDB (si >$200/mes)

2. **Model Optimization**
   - Fine-tune modelo propio (reduce costos 70%)
   - Hybrid: Modelo propio + Gemini fallback

3. **CDN & Edge**
   - Cloudflare para assets estáticos
   - Edge functions para latencia

---

## Risk Analysis (CTO Perspective)

### Critical Risks

#### 1. Gemini API Price Increase
**Probability:** Medium (30%)
**Impact:** Critical (costos 10x)
**Mitigation:**
- Abstraer AI provider (no vendor lock-in)
- Tener plan B: OpenAI, Anthropic
- Negociar contrato enterprise con Google

#### 2. Free Tier Limits Exceeded
**Probability:** High (60% en 3 meses)
**Impact:** Medium (necesita upgrade)
**Mitigation:**
- Monitoreo proactivo
- Budget alerts
- Upgrade path claro

#### 3. MongoDB Storage Overflow
**Probability:** Medium (40%)
**Impact:** High (servicio down)
**Mitigation:**
- TTL automático (7 días free tier)
- Comprimir embeddings
- Alert a 80% capacity

---

## Recommendations (CTO)

### Immediate (Pre-Production)
1. ✅ **Implementar Monitoring**
   - MongoDB storage usage
   - Gemini token consumption
   - Render bandwidth

2. ✅ **Set Budget Alerts**
   - MongoDB > 400 MB → Email alert
   - Gemini > $10/mes → Email alert
   - Render bandwidth > 80 GB → Email alert

3. ✅ **Optimize Gemini Usage**
   - Ejecutar `/audit-rag` para reducir tokens
   - Implementar response caching
   - Target: -30% token usage

### Short-term (0-3 months)
1. **Pricing Strategy** (con CMO)
   - Free tier: 1000 queries/mes
   - Pro tier: $10/mes (10k queries)
   - Enterprise: Custom

2. **Cost Attribution**
   - Track costo por usuario
   - Identify heavy users
   - Optimize or upsell

3. **Infrastructure Monitoring**
   - Datadog/New Relic free tier
   - Custom dashboard

### Medium-term (3-6 months)
1. **Evaluate Migration**
   - Si MongoDB > $100/mes → Considerar self-hosted
   - Si Render > $50/mes → Evaluar AWS

2. **Caching Layer**
   - Redis (Upstash free tier)
   - 40% reduction en Gemini calls

3. **Model Optimization**
   - A/B test: Flash vs Pro
   - ROI analysis

---

## Current Status (Beta)

### Infrastructure Health
- ✅ Render: Healthy (0% capacity)
- ✅ MongoDB: Healthy (~50 MB / 512 MB)
- ✅ Gemini: Low usage (<$5/mes)

### Bottlenecks
- ⚠️ Render sleep (15 min inactivity)
- ⚠️ MongoDB connection limits (free tier)
- ✅ Gemini latency: Acceptable (~1-2s)

### Next Milestones
1. **50 users:** Mantener free tiers
2. **100 users:** Upgrade Render ($7/mes)
3. **200 users:** Upgrade MongoDB ($57/mes)
4. **500 users:** Full paid stack (~$223/mes)

---

## Decision Log

### 2026-01-15: Mantener Free Tiers para Beta
**Context:** Un cliente en marcha blanca
**Decision:** Usar free tiers hasta validar PMF
**Rationale:** 
- Burn rate = $0
- Runway infinito
- Suficiente para 50-100 users

**Review Date:** 2026-04-15 (o cuando lleguemos a 100 users)

---

## Cost per User Analysis

### Current (Beta)
- **Cost:** $0/mes
- **Users:** 1
- **CPU (Cost Per User):** $0

### Target (PMF)
- **Cost:** $223/mes
- **Users:** 500
- **CPU:** $0.45/user
- **Revenue Target:** $10/user
- **Margin:** 95.5% 🎯

### At Scale
- **Cost:** $603/mes
- **Users:** 1000
- **CPU:** $0.60/user
- **Revenue Target:** $15/user
- **Margin:** 96% 🎯

**Conclusion:** Unit economics son excelentes. Gemini es el mayor costo variable, pero escalable.

---

## Action Items (CTO)

- [ ] Implementar monitoring de costos
- [ ] Configurar budget alerts
- [ ] Ejecutar `/audit-rag` para optimizar tokens
- [ ] Documentar upgrade path (free → paid)
- [ ] Evaluar caching strategy (Redis)
- [ ] Negociar con Google (enterprise pricing)

---

**Last Updated:** 2026-01-15
**Next Review:** 2026-02-15 (o al llegar a 50 users)
