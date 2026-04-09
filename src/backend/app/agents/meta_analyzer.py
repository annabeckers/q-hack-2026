import json
import structlog
from typing import List
from pydantic import BaseModel, Field

from app.agents.strands_agent import _build_model
from strands import Agent

log = structlog.get_logger()

class MetaAnalysisResult(BaseModel):
    risk_score: int = Field(..., description="Overall risk score from 0-100 (100 being worst).")
    risk_factors: List[str] = Field(..., description="List of 1-3 concise reasons for the score if >0.")
    summary: str = Field(..., description="A 1-2 sentence summary of the security posture of this chat.")

META_SYSTEM_PROMPT = (
    "You are an expert cybersecurity meta-analyzer. Your job is to take raw security findings "
    "from a single employee AI conversation and synthesize a risk score and summary. "
    "Respond ONLY with valid JSON strictly matching this schema: "
    '{"risk_score": int, "risk_factors": ["string"], "summary": "string"}. '
    "Do not include markdown blocks or any other text outside the JSON."
)

async def run_meta_analysis(findings_data: str) -> MetaAnalysisResult:
    """Run meta-analysis on a batch of findings to generate a ConversationInsight.
    
    Args:
        findings_data: A string representation of all findings for this chat.
    
    Returns:
        MetaAnalysisResult parsed from JSON.
    """
    model = _build_model()
    agent = Agent(
        model=model,
        system_prompt=META_SYSTEM_PROMPT,
    )
    
    prompt = f"Analyze these findings and return the JSON:\n\n{findings_data}"
    log.info("meta_analyzer_start", prompt_length=len(prompt))
    
    # We don't use async here as strands agent call is sync
    result = agent(prompt)
    response_text = str(result).strip()
    
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
        
    try:
        parsed = json.loads(response_text)
        meta_result = MetaAnalysisResult(**parsed)
    except Exception as e:
        log.error("meta_analyzer_parse_error", error=str(e), response=response_text)
        # Fallback
        meta_result = MetaAnalysisResult(
            risk_score=0,
            risk_factors=["Meta-analyzer failed to parse findings"],
            summary="Error analyzing findings."
        )
        
    log.info("meta_analyzer_done", score=meta_result.risk_score)
    return meta_result
