import logging
import os

import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from .executor import CustomerSupportAgentExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "9999"))
SERVER_URL = os.getenv("SERVER_URL", f"http://localhost:{PORT}")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL")

if __name__ == '__main__':
    # Define agent skills
    support_skill = AgentSkill(
        id='customer_support',
        name='Airline Customer Support',
        description='Airline customer support: seat changes, flight cancellations, baggage, and special requests',
        tags=['customer support', 'airline', 'booking'],
        examples=[
            'I want to change my seat',
            'Help me cancel my flight',
            'I need additional assistance',
            'What is my loyalty status?'
        ],
    )

    # Create public agent card
    public_agent_card = AgentCard(
        name='Customer Support Agent',
        description='Airline customer support agent for elite travelers',
        url=SERVER_URL,
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(),
        skills=[support_skill],
        supports_authenticated_extended_card=False,
    )

    # Create executor
    executor = CustomerSupportAgentExecutor()

    # Create request handler with agent executor
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    # Create A2A application
    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
    )

    logger.info(f"Starting Customer Support A2A Agent on port {PORT}")
    uvicorn.run(server.build(), host='0.0.0.0', port=PORT)
