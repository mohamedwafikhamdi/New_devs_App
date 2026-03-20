from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/dashboard/properties")
async def get_dashboard_properties(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, str]]:
    """Return the list of properties belonging to the current user's tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        from app.core.database_pool import DatabasePool
        from sqlalchemy import text

        db_pool = DatabasePool()
        await db_pool.initialize()

        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                query = text(
                    "SELECT id, name FROM properties WHERE tenant_id = :tenant_id ORDER BY id"
                )
                result = await session.execute(query, {"tenant_id": tenant_id})
                rows = result.fetchall()
                return [{"id": row.id, "name": row.name} for row in rows]
    except Exception as e:
        logger.error(f"Failed to fetch properties for tenant {tenant_id}: {e}")

    return []


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    total_revenue_float = round(float(revenue_data['total']), 2)
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
