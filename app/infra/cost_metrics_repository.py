"""
Repository for cost metrics data access.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pymongo import ASCENDING, DESCENDING

from app.infra.mongo_client import get_mongo_client
from app.config import settings


class CostMetricsRepository:
    """Repository for cost metrics persistence."""
    
    def create_indexes(self) -> None:
        """Create necessary indexes for efficient queries."""
        client = get_mongo_client()
        db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        collection = db.cost_metrics
        
        collection.create_index([("timestamp", DESCENDING)])
        collection.create_index([
            ("user_id", ASCENDING),
            ("timestamp", DESCENDING)
        ])
        collection.create_index([
            ("project_id", ASCENDING),
            ("timestamp", DESCENDING)
        ])
    
    def insert_usage(self, metric: Dict[str, Any]) -> None:
        """Insert a usage metric."""
        client = get_mongo_client()
        db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        
        db.cost_metrics.insert_one(metric)
    
    def get_metrics_by_date_range(
        self,
        start_date: datetime,
        metric_type: str = "gemini_usage"
    ) -> List[Dict[str, Any]]:
        """Get all metrics within a date range."""
        client = get_mongo_client()
        db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        
        return list(db.cost_metrics.find({
            "timestamp": {"$gte": start_date},
            "type": metric_type
        }))
    
    def get_metrics_by_user(
        self,
        user_id: str,
        start_date: datetime,
        metric_type: str = "gemini_usage"
    ) -> List[Dict[str, Any]]:
        """Get metrics for a specific user."""
        client = get_mongo_client()
        db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        
        return list(db.cost_metrics.find({
            "user_id": user_id,
            "timestamp": {"$gte": start_date},
            "type": metric_type
        }))
    
    def aggregate_daily_costs(
        self,
        start_date: datetime
    ) -> List[Dict[str, Any]]:
        """Aggregate costs by day."""
        client = get_mongo_client()
        db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        
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
        return list(db.cost_metrics.aggregate(pipeline))
    
    def aggregate_user_costs(
        self,
        user_id: str,
        start_date: datetime
    ) -> Dict[str, Any]:
        """Aggregate costs for a specific user."""
        client = get_mongo_client()
        db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        
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
        results = list(db.cost_metrics.aggregate(pipeline))
        return results[0] if results else None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get database storage statistics."""
        client = get_mongo_client()
        db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        
        return db.command("dbStats")
    
    def get_collection_counts(self) -> Dict[str, int]:
        """Get document counts for all collections."""
        client = get_mongo_client()
        db_name = settings.mongo_uri.split("/")[-1].split("?")[0]
        db = client[db_name]
        
        return {
            name: db[name].estimated_document_count()
            for name in db.list_collection_names()
        }
