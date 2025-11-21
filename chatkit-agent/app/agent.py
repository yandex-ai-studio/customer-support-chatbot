from __future__ import annotations

import os

from agents import Agent, FileSearchTool, Runner, RunConfig, OpenAIProvider, RunResultStreaming
from agents.mcp import MCPServer

FOLDER_ID = os.environ.get('FOLDER_ID')
API_KEY = os.environ.get('API_KEY')

SUPPORT_AGENT_INSTRUCTIONS = """
You are a friendly and efficient airline customer support agent.
You help elite flyers with seat changes, cancellations, checked bags, and
special requests. Follow these guidelines:

- Always acknowledge the customer's loyalty status and recent travel plans.
- When a task requires action, call the appropriate tool instead of describing
  the change hypothetically.
- After using a tool, confirm the outcome and offer next steps.
- If you cannot fulfill a request, apologise and suggest an alternative.
- Keep responses concise (2-3 sentences) unless extra detail is required.

Only use information provided in the customer context or tool results.
Use context_id from the request as customer profile id. 
Do not invent confirmation numbers or policy details.
""".strip()


class CustomerSupportAgent:

    def __init__(self, airline_mcp_server: MCPServer):
        self.agent = Agent(
            model=f"gpt://{FOLDER_ID}/yandexgpt/latest",
            name="Airline Customer Support Concierge",
            instructions=SUPPORT_AGENT_INSTRUCTIONS,
            mcp_servers=[airline_mcp_server],
            tools=[
                FileSearchTool(
                    max_num_results=3,
                    vector_store_ids=[os.environ.get('VECTOR_STORE_ID')],
                )
            ],
        )

        self.run_config = RunConfig(
            model_provider=OpenAIProvider(
                api_key=API_KEY,
                project=FOLDER_ID,
                base_url="https://rest-assistant.api.cloud.yandex.net/v1",
                use_responses=True
            )
        )

    def invoke(self, message, context, previous_response_id) -> RunResultStreaming:
        return Runner.run_streamed(
            self.agent,
            message,
            context=context,
            run_config=self.run_config,
            previous_response_id=previous_response_id,
        )
