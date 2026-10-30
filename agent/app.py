import asyncio
import json
import os

from agent.dial_client import DialClient
from agent.mcp_client import MCPClient
from agent.models.message import Message, Role
from agent.prompts import SYSTEM_PROMPT

DIAL_URL = "https://ai-proxy.lab.epam.com"
API_KEY = os.getenv("DIAL_API_KEY", "")

# https://remote.mcpservers.org/fetch/mcp
# Pay attention that `fetch` doesn't have resources and prompts


async def main():
    # TODO:
    # 1. Create MCP client and open connection to the MCP server (use `async with {YOUR_MCP_CLIENT} as mcp_client`),
    #    mcp_server_url="http://localhost:8005/mcp"
    # 2. Get Available MCP Resources and print them
    # 3. Get Available MCP Tools, assign to `tools` variable, print tool as well
    # 4. Create DialClient
    # 5. Create list with messages and add there SYSTEM_PROMPT with instructions to LLM
    # 6. Add to messages Prompts from MCP server as User messages
    # 7. Create console chat (infinite loop + ability to exit from chat + preserve message history after the call to dial client)
    async with MCPClient(mcp_server_url="http://localhost:8005/mcp") as mcp_client:
        tools = await mcp_client.get_tools()
        resources = await mcp_client.get_resources()
        tools_json = json.dumps(tools, indent=2)
        resources_json = json.dumps(
            [r.model_dump(mode="json") for r in resources], indent=2
        )
        print(f"Available Tools:\n{tools_json}\n")
        print(f"Available Resources:\n{resources_json}\n")

        prompts = await mcp_client.get_prompts()
        print("Available prompts:")
        for i, p in enumerate(prompts, 1):
            print(f"  {i}. {p.name} - {p.description}")
        choice = input("Choose a task (0 = plain chat): ")
        task_prompt = None
        if choice.isdigit() and 0 < int(choice) <= len(prompts):
            picked = prompts[int(choice) - 1]
            task_prompt = await mcp_client.get_prompt(picked.name)
            print(task_prompt[:300])

        dial_client = DialClient(
            api_key=API_KEY,
            endpoint=DIAL_URL,
            mcp_client=mcp_client,
            tools=tools,
        )
        messages = [
            Message(
                role=Role.SYSTEM,
                content=SYSTEM_PROMPT,
            )
        ]

        if task_prompt:
            messages.append(Message(role=Role.USER, content=task_prompt))

        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting chat...")
                break
            messages.append(Message(role=Role.USER, content=user_input))
            ai_message = await dial_client.get_completion(messages)
            messages.append(ai_message)


if __name__ == "__main__":
    asyncio.run(main())
