import json
import structlog
from typing import List
from pydantic import BaseModel, Field

from app.agents.strands_agent import _build_model
from strands import Agent

log = structlog.get_logger("recommender-agent")

class RecommendationItem(BaseModel):
    category: str = Field(..., description="One of: 'security', 'cost', 'compliance', 'training'")
    title: str = Field(..., description="Short, punchy title for the recommendation")
    description: str = Field(..., description="Detailed explanation of the issue and the proposed fix")
    impact_score: int = Field(..., description="Score from 0-100 indicating importance (100 is critical)")
    target_audience: str = Field(..., description="Target department or team (e.g. 'Engineering', 'HR', 'All Staff')")

class RecommendationResult(BaseModel):
    recommendations: List[RecommendationItem]

RECOMMENDER_SYSTEM_PROMPT = (
    "You are the Argus Executive Recommender. Your job is to analyze aggregate platform usage "
    "and security statistics, and output 2-5 highly actionable, strategic business recommendations.\n\n"
    "CRITICAL DIRECTIVES:\n"
    "- If you see sensitive data (API secrets, PII, financial data) being sent to US-hosted "
    "or cloud models (like OpenAI, Anthropic, or Gemini), YOU MUST strongly recommend switching "
    "those specific use cases to local AI (e.g. Ollama) or strict EU-hosted sovereign models to "
    "ensure compliance and data sovereignty.\n"
    "- If you see expensive models being used for trivial text tasks, recommend cheaper models.\n"
    "- If you see a specific department leaking secrets frequently, recommend targeted training.\n\n"
    "Respond ONLY with valid JSON strictly matching this schema: "
    '{"recommendations": [{"category": "string", "title": "string", "description": "string", "impact_score": int, "target_audience": "string"}]}. '
    "Do not include markdown or other text."
)

async def run_recommendation_agent(aggregate_stats: str) -> List[RecommendationItem]:
    """Run the recommender agent over aggregate platform statistics.
    
    Args:
        aggregate_stats: JSON string containing metrics from materialized views.
        
    Returns:
        List of generated Pydantic RecommendationItem objects.
    """
    model = _build_model()
    agent = Agent(
        model=model,
        system_prompt=RECOMMENDER_SYSTEM_PROMPT,
    )
    
    prompt = f"Analyze these platform statistics and generate executive recommendations in JSON:\n\n{aggregate_stats}"
    log.info("recommender_start", prompt_length=len(prompt))
    
    result = agent(prompt)
    response_text = str(result).strip()
    
    # Clean markdown
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
        
    try:
        parsed = json.loads(response_text)
        recs = RecommendationResult(**parsed).recommendations
    except Exception as e:
        log.error("recommender_parse_error", error=str(e), response=response_text)
        recs = []
        
    log.info("recommender_done", count=len(recs))
    return recs
