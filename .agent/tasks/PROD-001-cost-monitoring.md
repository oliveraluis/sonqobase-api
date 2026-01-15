# 📊 Cost Monitoring Implementation

## Objective
Track Gemini API usage, MongoDB storage, and Render bandwidth to prevent cost surprises and optimize spending.

## Implementation

### 1. Gemini Token Tracking

#### Create Monitoring Service
**File:** `app/services/cost_monitoring.py`

```python
"""
Cost monitoring service for tracking API usage and costs.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.infra.mongo_client import get_mongo_client


class CostMonitoringService:
    """Tracks costs and usage metrics."""
    
    def __init__(self):
        self.db = get_mongo_client()
        self.metrics_collection = self.db.cost_metrics
    
    async def log_gemini_usage(
        self,
        user_id: str,
        project_id: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "gemini-1.5-flash"
    ) -> None:
        """
        Log Gemini API usage for cost tracking.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model used
        """
        # Pricing (as of 2026-01-15)
        PRICING = {
            "gemini-1.5-flash": {
                "input": 0.075 / 1_000_000,  # per token
                "output": 0.30 / 1_000_000
            }
        }
        
        pricing = PRICING.get(model, PRICING["gemini-1.5-flash"])
        input_cost = input_tokens * pricing["input"]
        output_cost = output_tokens * pricing["output"]
        total_cost = input_cost + output_cost
        
        metric = {
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "project_id": project_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": total_cost,
            "type": "gemini_usage"
        }
        
        await self.metrics_collection.insert_one(metric)
    
    async def get_daily_costs(self, days: int = 7) -> Dict[str, Any]:
        """
        Get daily cost breakdown for the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with daily costs
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date},
                    "type": "gemini_usage"
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp"
                        }
                    },
                    "total_cost": {"$sum": "$total_cost_usd"},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "query_count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        results = await self.metrics_collection.aggregate(pipeline).to_list(None)
        
        return {
            "period_days": days,
            "daily_breakdown": results,
            "total_cost": sum(r["total_cost"] for r in results),
            "total_queries": sum(r["query_count"] for r in results)
        }
    
    async def get_user_costs(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get cost breakdown for a specific user."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "timestamp": {"$gte": start_date},
                    "type": "gemini_usage"
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_cost": {"$sum": "$total_cost_usd"},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "query_count": {"$sum": 1}
                }
            }
        ]
        
        result = await self.metrics_collection.aggregate(pipeline).to_list(1)
        
        if not result:
            return {
                "user_id": user_id,
                "total_cost": 0,
                "total_tokens": 0,
                "query_count": 0
            }
        
        return {
            "user_id": user_id,
            **result[0]
        }
    
    async def check_budget_alerts(self) -> list[Dict[str, Any]]:
        """
        Check if any budget thresholds are exceeded.
        
        Returns:
            List of alerts
        """
        alerts = []
        
        # Daily budget alert ($5/day)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        today_cost = await self.get_daily_costs(days=1)
        
        if today_cost["total_cost"] > 5:
            alerts.append({
                "severity": "warning",
                "type": "daily_budget",
                "message": f"Daily Gemini cost exceeded $5: ${today_cost['total_cost']:.2f}",
                "cost": today_cost["total_cost"]
            })
        
        # Monthly budget alert ($50/month)
        monthly_cost = await self.get_daily_costs(days=30)
        
        if monthly_cost["total_cost"] > 50:
            alerts.append({
                "severity": "critical",
                "type": "monthly_budget",
                "message": f"Monthly Gemini cost exceeded $50: ${monthly_cost['total_cost']:.2f}",
                "cost": monthly_cost["total_cost"]
            })
        
        return alerts
```

#### Integrate into RAG Query Service
**File:** `app/services/rag_query.py`

Add monitoring after each Gemini call:

```python
from app.services.cost_monitoring import CostMonitoringService

# After Gemini API call
cost_monitor = CostMonitoringService()
await cost_monitor.log_gemini_usage(
    user_id=user_id,
    project_id=project_id,
    input_tokens=response.usage_metadata.prompt_token_count,
    output_tokens=response.usage_metadata.candidates_token_count,
    model="gemini-1.5-flash"
)
```

---

### 2. MongoDB Storage Monitoring

#### Add Storage Check Endpoint
**File:** `app/api/v1/admin.py`

```python
from fastapi import APIRouter, Depends
from app.dependencies.auth import require_admin
from app.infra.mongo_client import get_mongo_client

router = APIRouter()

@router.get("/storage-stats")
async def get_storage_stats(admin=Depends(require_admin)):
    """Get MongoDB storage statistics."""
    db = get_mongo_client()
    
    stats = await db.command("dbStats")
    
    # Free tier limit: 512 MB
    FREE_TIER_LIMIT = 512 * 1024 * 1024  # bytes
    
    usage_mb = stats["dataSize"] / (1024 * 1024)
    usage_percent = (stats["dataSize"] / FREE_TIER_LIMIT) * 100
    
    return {
        "storage_mb": usage_mb,
        "storage_limit_mb": 512,
        "usage_percent": usage_percent,
        "alert": usage_percent > 80,
        "collections": {
            name: await db[name].estimated_document_count()
            for name in await db.list_collection_names()
        }
    }
```

---

### 3. Cost Dashboard Endpoint

**File:** `app/api/v1/admin.py`

```python
@router.get("/cost-dashboard")
async def get_cost_dashboard(admin=Depends(require_admin)):
    """Get comprehensive cost dashboard."""
    cost_monitor = CostMonitoringService()
    
    # Gemini costs
    daily_costs = await cost_monitor.get_daily_costs(days=7)
    monthly_costs = await cost_monitor.get_daily_costs(days=30)
    
    # MongoDB storage
    db = get_mongo_client()
    db_stats = await db.command("dbStats")
    storage_mb = db_stats["dataSize"] / (1024 * 1024)
    
    # Budget alerts
    alerts = await cost_monitor.check_budget_alerts()
    
    return {
        "gemini": {
            "last_7_days": daily_costs,
            "last_30_days": monthly_costs,
            "avg_cost_per_query": monthly_costs["total_cost"] / max(monthly_costs["total_queries"], 1)
        },
        "mongodb": {
            "storage_mb": storage_mb,
            "limit_mb": 512,
            "usage_percent": (storage_mb / 512) * 100
        },
        "render": {
            "note": "Check Render dashboard for bandwidth usage"
        },
        "alerts": alerts,
        "total_monthly_estimate": monthly_costs["total_cost"]
    }
```

---

### 4. Scheduled Budget Alerts

**File:** `app/tasks/budget_alerts.py`

```python
"""
Scheduled task to check budget alerts daily.
"""
import asyncio
from datetime import datetime
from app.services.cost_monitoring import CostMonitoringService
from app.infra.email_client import send_email  # If you have email setup


async def check_and_send_budget_alerts():
    """Check budget and send alerts if thresholds exceeded."""
    cost_monitor = CostMonitoringService()
    alerts = await cost_monitor.check_budget_alerts()
    
    if alerts:
        # Log alerts
        for alert in alerts:
            print(f"[BUDGET ALERT] {alert['severity'].upper()}: {alert['message']}")
        
        # TODO: Send email notification
        # await send_email(
        #     to="admin@sonqobase.com",
        #     subject="SonqoBase Budget Alert",
        #     body="\n".join(a["message"] for a in alerts)
        # )
    
    return alerts


# Run this daily via cron or scheduler
if __name__ == "__main__":
    asyncio.run(check_and_send_budget_alerts())
```

---

## Testing

### Test Cost Tracking
```python
# Test in development
from app.services.cost_monitoring import CostMonitoringService

monitor = CostMonitoringService()

# Log test usage
await monitor.log_gemini_usage(
    user_id="test_user",
    project_id="test_project",
    input_tokens=1000,
    output_tokens=500,
    model="gemini-1.5-flash"
)

# Check costs
costs = await monitor.get_daily_costs(days=1)
print(f"Today's cost: ${costs['total_cost']:.4f}")
```

---

## Deployment

1. **Create MongoDB index** for efficient queries:
```python
await db.cost_metrics.create_index([("timestamp", -1)])
await db.cost_metrics.create_index([("user_id", 1), ("timestamp", -1)])
```

2. **Setup cron job** for daily alerts:
```bash
# Run daily at 9 AM
0 9 * * * cd /app && python app/tasks/budget_alerts.py
```

3. **Monitor dashboard** at `/api/v1/admin/cost-dashboard`

---

## Expected Impact

- ✅ **Visibility:** Know exactly how much Gemini costs daily
- ✅ **Alerts:** Get notified before exceeding budget
- ✅ **Attribution:** Track cost per user/project
- ✅ **Optimization:** Identify heavy users for upsell or optimization

**Estimated Time:** 4-6 hours
**Priority:** High (PROD-001)
