import json
import structlog
from sqlalchemy import text
from app.infrastructure.database import async_session_factory
from app.agents.recommender import run_recommendation_agent

log = structlog.get_logger("recommendation-engine")

async def generate_system_recommendations() -> int:
    """Generate system-level recommendations using aggregate data and Strands agent.
    
    Returns:
        Number of active recommendations generated/updated.
    """
    async with async_session_factory() as session:
        # Fetch stats to feed the LLM
        query = text("""
            SELECT 
                (SELECT row_to_json(r) FROM (SELECT * FROM mv_dashboard_overview) r) as overview,
                (SELECT json_agg(r) FROM (SELECT * FROM mv_findings_by_category LIMIT 10) r) as findings_cat,
                (SELECT json_agg(r) FROM (SELECT * FROM mv_provider_stats LIMIT 10) r) as provider_stats
        """)
        
        result = await session.execute(query)
        row = result.fetchone()
        
        if not row or not row.overview:
            log.info("recommendation_engine_skip", reason="no data")
            return 0
            
        stats_data = {
            "overview": row.overview,
            "top_finding_categories": row.findings_cat or [],
            "provider_usage_and_leaks": row.provider_stats or []
        }
        
    stats_json = json.dumps(stats_data, indent=2)
    
    log.info("recommendation_engine_started", stats_size=len(stats_json))
    
    # 1. Run the Strands Agent
    recommendations = await run_recommendation_agent(stats_json)
    
    if not recommendations:
        log.warning("recommendation_engine_empty_result")
        return 0
        
    # 2. Persist the new recommendations
    async with async_session_factory() as session:
        # Mark old active recommendations as historical
        await session.execute(text("UPDATE system_recommendations SET status = 'historical' WHERE status = 'active'"))
        
        # Insert new active recommendations
        insert_query = text("""
            INSERT INTO system_recommendations 
            (category, title, description, impact_score, target_audience, status)
            VALUES (:category, :title, :description, :impact, :audience, 'active')
        """)
        
        for rec in recommendations:
            await session.execute(insert_query, {
                "category": rec.category,
                "title": rec.title,
                "description": rec.description,
                "impact": rec.impact_score,
                "audience": rec.target_audience
            })
            
        await session.commit()
        
    log.info("recommendation_engine_complete", count=len(recommendations))
    return len(recommendations)
