"""
Script de prueba para validar cost monitoring localmente.
"""
import asyncio
from app.services.cost_monitoring import CostMonitoringService


async def test_cost_monitoring():
    """Test básico de cost monitoring."""
    print("🧪 Testing Cost Monitoring Service\n")
    
    service = CostMonitoringService()
    
    # 1. Crear índices
    print("1️⃣ Creating MongoDB indexes...")
    service.create_indexes()
    print("✅ Indexes created\n")
    
    # 2. Log de prueba (simular uso de Gemini)
    print("2️⃣ Logging test Gemini usage...")
    await service.log_gemini_usage(
        user_id="test_user_123",
        project_id="test_project_456",
        input_tokens=1000,
        output_tokens=500,
        model="gemini-2.5-flash"
    )
    print("✅ Usage logged\n")
    
    # 3. Verificar costos diarios
    print("3️⃣ Getting daily costs...")
    daily_costs = await service.get_daily_costs(days=1)
    print(f"Daily costs: ${daily_costs['total_cost']:.4f}")
    print(f"Total queries: {daily_costs['total_queries']}")
    print(f"Avg cost per query: ${daily_costs['avg_cost_per_query']:.4f}\n")
    
    # 4. Verificar costos por usuario
    print("4️⃣ Getting user costs...")
    user_costs = await service.get_user_costs("test_user_123", days=30)
    print(f"User total cost: ${user_costs['total_cost']:.4f}")
    print(f"User queries: {user_costs['query_count']}\n")
    
    # 5. Verificar storage
    print("5️⃣ Getting storage stats...")
    storage = await service.get_storage_stats()
    print(f"MongoDB usage: {storage['storage_mb']:.2f} MB / {storage['storage_limit_mb']} MB")
    print(f"Usage: {storage['usage_percent']:.1f}%")
    print(f"Alert: {'⚠️ YES' if storage['alert'] else '✅ NO'}\n")
    
    # 6. Verificar alertas
    print("6️⃣ Checking budget alerts...")
    alerts = await service.check_budget_alerts()
    if alerts:
        for alert in alerts:
            print(f"🚨 {alert['severity'].upper()}: {alert['message']}")
    else:
        print("✅ No budget alerts\n")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_cost_monitoring())
