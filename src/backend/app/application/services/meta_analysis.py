from __future__ import annotations

import json
import structlog
from sqlalchemy import text
from app.infrastructure.database import async_session_factory
from app.agents.meta_analyzer import run_meta_analysis

log = structlog.get_logger("meta-analysis-service")

async def run_meta_analysis_for_pending_chats() -> int:
    """Finds chats with findings but no insight record, and runs the meta-analyzer on them."""
    insights_created = 0
    
    async with async_session_factory() as session:
        # Get chats that have findings but no insight record yet
        query = text("""
            SELECT f.chat_id, MAX(f.run_id) as run_id,
                   json_agg(json_build_object(
                       'analyzer', f.analyzer,
                       'category', f.category,
                       'severity', f.severity,
                       'snippet', f.snippet
                   )) as findings_json
            FROM findings f
            LEFT JOIN conversation_insights ci ON f.chat_id = ci.chat_id
            WHERE ci.id IS NULL
            GROUP BY f.chat_id
            LIMIT 10
        """)
        
        result = await session.execute(query)
        pending_chats = result.fetchall()
        
        if not pending_chats:
            return 0
            
        log.info("meta_analysis_batch_started", count=len(pending_chats))
        
        for row in pending_chats:
            chat_id = row[0]
            run_id = row[1]
            findings = row[2]
            
            # Format findings for the prompt
            findings_text = json.dumps(findings, indent=2)
            
            # Run the agent
            meta_result = await run_meta_analysis(findings_text)
            
            # Insert into database
            insert_query = text("""
                INSERT INTO conversation_insights (chat_id, run_id, risk_score, risk_factors, summary)
                VALUES (:chat_id, :run_id, :risk_score, :risk_factors, :summary)
            """)
            
            await session.execute(insert_query, {
                "chat_id": chat_id,
                "run_id": run_id,
                "risk_score": meta_result.risk_score,
                "risk_factors": json.dumps(meta_result.risk_factors),
                "summary": meta_result.summary
            })
            
            insights_created += 1
            
        await session.commit()
        log.info("meta_analysis_batch_complete", insights_created=insights_created)
        
    return insights_created
