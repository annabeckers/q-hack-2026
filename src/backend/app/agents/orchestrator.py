"""Agent orchestrator — deterministic sequencing of multiple agents.

Pattern extracted from AstroFarm/EDEN project. The orchestrator is NOT an LLM —
it's deterministic Python code that sequences agent calls, collects results,
and resolves decisions.
"""

import json
import structlog
from dataclasses import dataclass, field
from datetime import datetime, timezone

log = structlog.get_logger()


@dataclass
class AgentResponse:
    agent: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class OrchestratorSession:
    trigger: str
    responses: list[AgentResponse] = field(default_factory=list)
    decision: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentOrchestrator:
    """Sequences agent calls in a deterministic pipeline.

    Each agent sees the accumulated context from previous agents.
    The orchestrator decides flow — agents decide content.

    Usage:
        orchestrator = AgentOrchestrator()
        orchestrator.register("analyst", analyst_fn)
        orchestrator.register("planner", planner_fn)
        orchestrator.register("critic", critic_fn)
        result = await orchestrator.run("Analyze this dataset")
    """

    def __init__(self):
        self._agents: dict[str, callable] = {}
        self._pipeline: list[str] = []

    def register(self, name: str, agent_fn: callable) -> None:
        """Register an agent function.

        The function should accept (prompt: str) -> str.
        """
        self._agents[name] = agent_fn
        self._pipeline.append(name)

    async def run(self, trigger: str, context: dict | None = None) -> OrchestratorSession:
        """Run the full agent pipeline sequentially."""
        session = OrchestratorSession(trigger=trigger)
        accumulated_context = json.dumps(context) if context else ""

        for agent_name in self._pipeline:
            agent_fn = self._agents[agent_name]

            # Build prompt with accumulated context
            prompt = f"Task: {trigger}"
            if accumulated_context:
                prompt += f"\n\nContext: {accumulated_context}"
            if session.responses:
                prev = "\n".join(
                    f"[{r.agent}]: {r.content}" for r in session.responses
                )
                prompt += f"\n\nPrevious agents:\n{prev}"

            log.info("agent_call", agent=agent_name, trigger=trigger)

            try:
                result = await agent_fn(prompt)
                response = AgentResponse(agent=agent_name, content=str(result))
                session.responses.append(response)
                log.info("agent_response", agent=agent_name, length=len(str(result)))
            except Exception as e:
                log.error("agent_error", agent=agent_name, error=str(e))
                session.responses.append(
                    AgentResponse(agent=agent_name, content=f"ERROR: {e}")
                )

        # Simple resolution: last agent's response is the decision
        if session.responses:
            session.decision = session.responses[-1].content

        return session

    @classmethod
    def from_yaml(cls, config_path: str = "config/app.yaml") -> "AgentOrchestrator":
        """Build an orchestrator from YAML config.

        Reads the agents.orchestrator section from app.yaml and creates
        agent functions using the registry for each configured agent.

        Example config:
            agents:
              orchestrator:
                mode: sequential
                agents:
                  - name: analyst
                    framework: anthropic
                    system: "You analyze data."
        """
        import yaml
        from pathlib import Path
        from app.agents.registry import AgentFramework, invoke_agent

        config_file = Path(config_path)
        if not config_file.exists():
            log.warning("orchestrator_config_not_found", path=config_path)
            return cls()

        with open(config_file) as f:
            config = yaml.safe_load(f)

        orch_config = config.get("agents", {}).get("orchestrator", {})
        agent_defs = orch_config.get("agents", [])

        instance = cls()
        for agent_def in agent_defs:
            name = agent_def["name"]
            framework = AgentFramework(agent_def.get("framework", "anthropic"))
            system = agent_def.get("system", "")

            async def make_agent_fn(prompt, fw=framework, sys=system):
                return await invoke_agent(fw, prompt, sys)

            instance.register(name, make_agent_fn)

        return instance

    async def run_parallel(self, trigger: str) -> OrchestratorSession:
        """Run all agents in parallel (no context accumulation)."""
        import asyncio

        session = OrchestratorSession(trigger=trigger)

        async def call_agent(name: str) -> AgentResponse:
            fn = self._agents[name]
            result = await fn(f"Task: {trigger}")
            return AgentResponse(agent=name, content=str(result))

        results = await asyncio.gather(
            *[call_agent(name) for name in self._pipeline],
            return_exceptions=True,
        )

        for r in results:
            if isinstance(r, Exception):
                session.responses.append(AgentResponse(agent="error", content=str(r)))
            else:
                session.responses.append(r)

        return session
