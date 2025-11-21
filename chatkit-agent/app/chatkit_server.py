from __future__ import annotations

import os
from typing import Any, AsyncIterator

from agents.mcp import MCPServerSse
from chatkit.agents import AgentContext, stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.store import Store
from chatkit.types import (
    ClientToolCallItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)

from .agent import CustomerSupportAgent
from .airline_client import get_customer_profile

DEFAULT_THREAD_ID = "demo_default_thread"
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8081")
API_KEY = os.environ.get('API_KEY')


class CustomerSupportServer(ChatKitServer[dict[str, Any]]):

    def __init__(
            self,
            store: Store,
    ) -> None:
        super().__init__(store)
        self.airline_mcp_server = MCPServerSse(
            name="Airline MCP Server",
            params={
                "url": MCP_SERVER_URL,
                "headers": {"Authorization": f"Api-Key {API_KEY}"}
            },
            cache_tools_list=True,
        )
        self.agent = CustomerSupportAgent(self.airline_mcp_server)

    async def respond(
            self,
            thread: ThreadMetadata,
            item: UserMessageItem,
            context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:

        if isinstance(item, ClientToolCallItem):
            return

        user_message = _user_message_text(item)
        profile_id = thread.id if thread and thread.id else DEFAULT_THREAD_ID

        # Fetch customer profile from airline-api service
        profile_prompt = await get_customer_profile(profile_id)

        # Combine prompt from the customer profile and user message
        combined_prompt = (
            f"{profile_prompt}\n\nCurrent request: {user_message}\n"
            "Respond as the airline support concierge."
        )

        # Create agent context
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        # Get previous_response_id from thread metadata
        metadata = thread.metadata if thread.metadata else {}
        previous_response_id = metadata.get("previous_response_id")

        await self.airline_mcp_server.connect()
        try:
            # Run the agent
            result = self.agent.invoke(
                combined_prompt,
                agent_context,
                previous_response_id,
            )

            # Stream result
            async for event in stream_agent_response(agent_context, result):
                yield event

            # Save previous_response_id to metadata for the next invocation
            if result.last_response_id is not None:
                metadata["previous_response_id"] = result.last_response_id
                thread.metadata = metadata
                await self.store.save_thread(thread, context)
        finally:
            await self.airline_mcp_server.cleanup()


def _user_message_text(item: UserMessageItem) -> str:
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()
