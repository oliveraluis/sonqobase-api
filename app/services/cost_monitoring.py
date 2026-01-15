"""
Cost monitoring service for tracking API usage and costs.

This service tracks Gemini API usage, MongoDB storage, and provides
budget alerts to prevent cost surprises.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.infra.cost_metrics_repository import CostMetricsRepository


class CostMonitoringService:
    """Tracks costs and usage metrics using MongoDB."""
    
    def __init__(self, repository: CostMetricsRepository = None):
        self.repository = repository or CostMetricsRepository()
    
    def log_gemini_usage(
        self,
        user_id: str,
        project_id: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "gemini-2.5-flash"
    ) -> None:
        """
        Log Gemini API usage for cost tracking.
        
        Args:
            user_id: User identifier
            project_id: Project identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model used (default: gemini-2.5-flash)
        """
        # Pricing as of 2026-01-15
        PRICING = {
            "gemini-2.5-flash": {
                "input": 0.075 / 1_000_000,  # $0.075 per 1M tokens
                "output": 0.30 / 1_000_000   # $0.30 per 1M tokens
            },
            "gemini-embedding-001": {
                "input": 0.00001 / 1_000,  # $0.00001 per 1k tokens (much cheaper)
                "output": 0  # Embeddings don't have output
            }
        }
        
        pricing = PRICING.get(model, PRICING["gemini-2.5-flash"])
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
        
        self.repository.insert_usage(metric)
    
    def get_daily_costs(self, days: int = 7) -> Dict[str, Any]:
        """
        Get daily cost breakdown for the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with daily costs and totals
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        results = self.repository.aggregate_daily_costs(start_date)
        
        return {
            "period_days": days,
            "daily_breakdown": results,
            "total_cost": sum(r["total_cost"] for r in results),
            "total_queries": sum(r["query_count"] for r in results),
            "avg_cost_per_query": sum(r["total_cost"] for r in results) / max(sum(r["query_count"] for r in results), 1)
        }
    
    def get_user_costs(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get cost breakdown for a specific user.
        
        Args:
            user_id: User identifier
            days: Number of days to look back
            
        Returns:
            Dictionary with user costs
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        result = self.repository.aggregate_user_costs(user_id, start_date)
        
        if not result:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_cost": 0,
                "total_tokens": 0,
                "query_count": 0
            }
        
        return {
            "user_id": user_id,
            "period_days": days,
            **result
        }
    
    def check_budget_alerts(self) -> List[Dict[str, Any]]:
        """
        Check if any budget thresholds are exceeded.
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        # Daily budget alert ($5/day)
        today_cost = self.get_daily_costs(days=1)
        
        if today_cost["total_cost"] > 5:
            alerts.append({
                "severity": "warning",
                "type": "daily_budget",
                "message": f"Daily Gemini cost exceeded $5: ${today_cost['total_cost']:.2f}",
                "cost": today_cost["total_cost"],
                "threshold": 5
            })
        
        # Monthly budget alert ($50/month)
        monthly_cost = self.get_daily_costs(days=30)
        
        if monthly_cost["total_cost"] > 50:
            alerts.append({
                "severity": "critical",
                "type": "monthly_budget",
                "message": f"Monthly Gemini cost exceeded $50: ${monthly_cost['total_cost']:.2f}",
                "cost": monthly_cost["total_cost"],
                "threshold": 50
            })
        
        return alerts
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get MongoDB storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        stats = self.repository.get_storage_stats()
        
        # Free tier limit: 512 MB
        FREE_TIER_LIMIT_MB = 512
        FREE_TIER_LIMIT_BYTES = FREE_TIER_LIMIT_MB * 1024 * 1024
        
        usage_mb = stats["dataSize"] / (1024 * 1024)
        usage_percent = (stats["dataSize"] / FREE_TIER_LIMIT_BYTES) * 100
        
        return {
            "storage_mb": round(usage_mb, 2),
            "storage_limit_mb": FREE_TIER_LIMIT_MB,
            "usage_percent": round(usage_percent, 2),
            "alert": usage_percent > 80,
            "collections": self.repository.get_collection_counts()
        }
    
    def create_indexes(self) -> None:
        """Create necessary indexes for efficient queries."""
        self.repository.create_indexes()
