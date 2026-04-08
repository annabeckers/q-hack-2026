"""GraphQL API — alternative to REST using Strawberry.

Enable by uncommenting the router in main.py.
Access at: http://localhost:8000/graphql (includes GraphiQL IDE).

Usage:
    query {
      health { status python }
      me { id email name }
    }

    mutation {
      agentInvoke(framework: "anthropic", prompt: "Hello") {
        response
        framework
      }
    }
"""

import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import Optional


@strawberry.type
class HealthInfo:
    status: str
    python: str


@strawberry.type
class UserInfo:
    id: str
    email: str
    name: str


@strawberry.type
class AgentResult:
    response: str
    framework: str


@strawberry.type
class Query:
    @strawberry.field
    async def health(self) -> HealthInfo:
        import sys
        return HealthInfo(status="ok", python=sys.version.split()[0])

    @strawberry.field
    async def me(self, info: strawberry.types.Info) -> Optional[UserInfo]:
        # TODO: Extract user from JWT in context
        return None


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def agent_invoke(self, framework: str = "anthropic", prompt: str = "") -> AgentResult:
        from app.agents.registry import AgentFramework, invoke_agent

        result = await invoke_agent(AgentFramework(framework), prompt)
        return AgentResult(response=result, framework=framework)


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema)
