from __future__ import annotations

import os

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import DataPart, Part
from a2a.utils import new_agent_text_message
from agents.mcp import MCPServerSse

from .agent import CustomerSupportAgent
from .airline_client import (
    fetch_customer_profile, get_customer_profile
)

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8081")
API_KEY = os.environ.get('API_KEY')


class CustomerSupportAgentExecutor(AgentExecutor):

    def __init__(self):
        self.airline_mcp_server = MCPServerSse(
            name="Airline MCP Server",
            params={
                "url": MCP_SERVER_URL,
                "headers": {"Authorization": f"Api-Key {API_KEY}"}
            },
            cache_tools_list=True,
        )
        self.agent = CustomerSupportAgent(self.airline_mcp_server)

    async def execute(
            self,
            context: RequestContext,
            event_queue: EventQueue,
    ) -> None:
        user_message = context.get_user_input()
        profile_id = context.context_id

        # Fetch customer profile from airline-api service
        profile_prompt = await get_customer_profile(profile_id)

        # Combine prompt from the customer profile and user message
        combined_prompt = (
            f"{profile_prompt}\n\nCurrent request: {user_message}\n"
            "Respond as the airline support concierge."
        )

        await self.airline_mcp_server.connect()
        try:
            # Run the agent
            result = await self.agent.invoke(combined_prompt)

            # Create message from result and profile
            message = new_agent_text_message(result)

            # Fetch updated customer profile
            updated_profile = await fetch_customer_profile(profile_id)

            # Add customer profile data to message
            message.parts.append(Part(root=DataPart(data=updated_profile)))

            # Add message to queue for sending to the client
            await event_queue.enqueue_event(message)

        finally:
            await self.airline_mcp_server.cleanup()

    async def cancel(
            self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel the current execution."""
        raise NotImplementedError()
