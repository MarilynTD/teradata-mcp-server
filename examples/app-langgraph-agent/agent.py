import asyncio
import os

import nest_asyncio
from dotenv import load_dotenv
from IPython.display import Markdown, display
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from prompts import SYSTEM_PROMPT

nest_asyncio.apply()
load_dotenv()

MCP_URL = os.getenv("MCP_URL", "https://teradata-mcp-server-xxx.run.app/mcp/")
MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")


class ChurnAnalyst:
    """Agente LangGraph para análisis de churn Telco via MCP Teradata."""

    def __init__(self):
        self.agent = None
        self._client = None
        self.memory = MemorySaver()
        self.thread_id = "telco-churn-demo"
        self.tools = []

    async def initialize(self):
        self._client = MultiServerMCPClient({
            "teradata": {
                "url": MCP_URL,
                "transport": "streamable_http",
            }
        })
        await self._client.__aenter__()
        self.tools = self._client.get_tools()

        llm = ChatAnthropic(
            model=MODEL,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0,
            max_tokens=4096,
        )

        self.agent = create_react_agent(
            llm,
            self.tools,
            prompt=SYSTEM_PROMPT,
            checkpointer=self.memory,
        )
        return self

    async def chat(self, message: str) -> str:
        config = {"configurable": {"thread_id": self.thread_id}}
        result = await self.agent.ainvoke(
            {"messages": [("user", message)]},
            config=config,
        )
        return result["messages"][-1].content

    def ask(self, message: str) -> str:
        """Wrapper síncrono para usar en notebooks: ejecuta, imprime y retorna la respuesta."""
        response = asyncio.run(self.chat(message))
        display(Markdown(response))
        return response

    def reset_memory(self):
        """Reinicia el historial de conversación."""
        self.memory = MemorySaver()
        self.thread_id = "telco-churn-demo"
        self.agent = create_react_agent(
            self.agent.nodes["agent"].bound,
            self.tools,
            prompt=SYSTEM_PROMPT,
            checkpointer=self.memory,
        )

    async def close(self):
        if self._client:
            await self._client.__aexit__(None, None, None)


def create_analyst() -> ChurnAnalyst:
    """Inicializa y retorna el agente listo para usar."""
    analyst = ChurnAnalyst()
    asyncio.run(analyst.initialize())
    print(f"✓ Agente inicializado con {len(analyst.tools)} herramientas MCP")
    print(f"✓ Modelo: {MODEL}")
    print(f"✓ MCP endpoint: {MCP_URL}")
    return analyst


if __name__ == "__main__":
    analyst = create_analyst()
    print("\nAgente Analista de Churn Telco listo.")
    print("Escribe 'salir' para terminar.\n")

    while True:
        query = input("Tu pregunta: ").strip()
        if query.lower() in ("salir", "exit", "quit"):
            break
        if not query:
            continue
        analyst.ask(query)
