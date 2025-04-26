import os
from google.adk.agents import Agent
from google.adk.tools.toolbox_tool import ToolboxTool

url = os.getenv("TOOLBOX_URL", "https://toolbox-640147180837.us-central1.run.app")
toolbox = ToolboxTool(url)

# Load single tool
# tools = toolbox.get_tool(tool_name='search-hotels-by-location'),
# Load all the tools
tools = toolbox.get_toolset(toolset_name='my_first_toolset')

root_agent = Agent(
    name="hotel_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about hotels in a city or hotels by name."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the hotels in a specific city or hotels by name. Use the tools to answer the question"
    ),
    tools=tools,
)