# 💰 Pricing Analysis - SonqoBase Current Plans

## Current Pricing Structure

### Free Tier - $0/mes
- 2 proyectos activos
- 500 lecturas/mes
- 500 escrituras/mes
- **50 consultas RAG/mes**
- PDFs hasta 5MB
- Duración: 2 días

### Starter Tier - $29/mes (Popular)
- 7 proyectos activos
- 5,000 lecturas/mes
- 2,500 escrituras/mes
- **500 consultas RAG/mes**
- PDFs hasta 25MB
- Duración: 7 días

### Pro Tier - $99/mes
- 15 proyectos activos
- 25,000 lecturas/mes
- 12,500 escrituras/mes
- **2,500 consultas RAG/mes**
- PDFs hasta 50MB
- Duración: 30 días
- Webhooks
- Soporte prioritario

---

## Cost Analysis vs Pricing

### Starter Tier ($29/mes)

**Costos Estimados:**
- 500 consultas RAG × $0.001 = $0.50 (Gemini)
- Storage (25MB PDFs) = $0.10
- Infrastructure = $0.05
- **Total Cost:** ~$0.65/user

**Margin:** ($29 - $0.65) / $29 = **97.8%** ✅

**Justification:**
- PDFs grandes (hasta 25MB) requieren más procesamiento
- Embeddings de PDFs grandes son costosos
- Valor percibido alto (RAG listo para usar)

---

### Pro Tier ($99/mes)

**Costos Estimados:**
- 2,500 consultas RAG × $0.001 = $2.50 (Gemini)
- Storage (50MB PDFs) = $0.20
- Infrastructure = $0.10
- Webhooks overhead = $0.05
- **Total Cost:** ~$2.85/user

**Margin:** ($99 - $2.85) / $99 = **97.1%** ✅

**Justification:**
- PDFs muy grandes (50MB) = procesamiento intensivo
- Webhooks agregan valor
- Soporte prioritario tiene costo operacional
- Target: Empresas que valoran tiempo

---

## Competitive Positioning

### vs Pinecone
- Pinecone Starter: $70/mes (solo vector DB)
- SonqoBase Starter: $29/mes (RAG completo)
- **Ventaja:** 58% más barato, más features

### vs OpenAI Assistants
- OpenAI: Pay-per-use, sin límites claros
- SonqoBase: Pricing predecible
- **Ventaja:** Transparencia, sin sorpresas

### Value Proposition
✅ **All-in-one:** PDF upload + embeddings + RAG queries
✅ **Ephemeral:** Auto-cleanup = menor costo
✅ **Predecible:** Límites claros, sin sorpresas
✅ **Rápido:** <5 min onboarding

---

## Recommendations (CEO + CMO)

### ✅ Keep Current Pricing
**Rationale:**
- Margins excelentes (97%+)
- Justificado por valor (PDFs grandes)
- Competitivo vs alternativas
- Pricing predecible (vs pay-per-use)

### ✅ Add Annual Plans
**Recommendation:**
- Starter: $290/año (save $58, 2 meses gratis)
- Pro: $990/año (save $198, 2 meses gratis)

**Benefits:**
- Mejor cash flow
- Reduce churn
- 17% discount incentivizes commitment

### ✅ Add-ons for Flexibility
**Extra Queries:**
- $10 por 500 consultas RAG adicionales (Starter)
- $20 por 1,000 consultas RAG adicionales (Pro)

**Extra Storage:**
- $5 por 10MB adicionales de PDFs

**Extended TTL:**
- $15/mes para 30 días (Starter tier)

---

## Revenue Projections (Realistic)

### Month 3 Post-Launch
- Free users: 100
- Starter users: 10 (10% conversion)
- Pro users: 2

**MRR:**
- Starter: 10 × $29 = $290
- Pro: 2 × $99 = $198
- **Total MRR:** $488

**Costs:** ~$30/month
**Profit:** $458/month
**Margin:** 94%

---

### Month 6 Post-Launch
- Free users: 300
- Starter users: 40
- Pro users: 10

**MRR:**
- Starter: 40 × $29 = $1,160
- Pro: 10 × $99 = $990
- **Total MRR:** $2,150

**Costs:** ~$150/month
**Profit:** $2,000/month
**Margin:** 93%

---

## Key Insights

### Why Higher Pricing Works

1. **Value-based, not cost-based**
   - Customers pay for outcome (RAG working), not just API calls
   - PDFs grandes = más valor extraído

2. **Target market can afford it**
   - Developers/companies building products
   - $29-99/mes es "rounding error" para empresas
   - Indie developers que valoran tiempo

3. **Anchoring effect**
   - Pro tier ($99) hace que Starter ($29) parezca barato
   - Free tier genera leads

4. **Margins permiten crecer**
   - 97% margin = mucho espacio para marketing
   - Puede ofrecer descuentos sin perder dinero
   - Puede invertir en features

---

## Action Items

- [x] Validar pricing actual (APROBADO)
- [ ] Agregar planes anuales (17% descuento)
- [ ] Crear página de pricing profesional
- [ ] Implementar add-ons para flexibilidad
- [ ] A/B test: Free tier con 50 vs 100 consultas

---

## CEO Decision

**Status:** ✅ APPROVED

**Pricing actual es excelente:**
- Margins >97%
- Competitivo
- Justificado por valor
- Predecible para clientes

**Next Steps:**
1. Mantener pricing actual
2. Agregar planes anuales
3. Implementar Stripe (PROD-007)
4. Monitorear conversion rates
5. Ajustar solo si conversion <5%

**Review Date:** 2026-04-15

---

**Last Updated:** 2026-01-15
**Owner:** CEO + CMO
