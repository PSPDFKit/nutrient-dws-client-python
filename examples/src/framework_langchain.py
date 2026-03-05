import asyncio
import os

from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from nutrient_dws import NutrientClient


client = NutrientClient(api_key=os.getenv("NUTRIENT_API_KEY", "api_key_placeholder"))


async def redact_emails(path: str) -> str:
    result = await client.create_redactions_ai(
        path,
        criteria="Redact all email addresses.",
        redaction_state="apply",
    )
    return str(result)


tool = StructuredTool.from_function(
    func=redact_emails,
    coroutine=redact_emails,
    name="redact_emails",
    description="Redact email addresses from a document using Nutrient DWS.",
)


async def main() -> None:
    model = ChatOpenAI(
        model="gpt-4.1-mini",
        api_key=os.getenv("OPENAI_API_KEY", "sk-placeholder"),
    )
    agent = create_react_agent(model, [tool])
    state = await agent.ainvoke(
        {"messages": [("user", "Redact emails from ./assets/sample.pdf.")]}
    )
    print(state["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
