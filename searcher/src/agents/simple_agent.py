from .interface import AgentBase

from src.llm_providers.interface import ChatProvider

import json
import logging

logger = logging.getLogger(__name__)


TOOL_CALL_RESULT_PROMPT = """
After calling tool with name: {name}
With arguments: {arguments}

Got result: {result}
"""


class SimpleAgnet(AgentBase):
    def __init__(self, chat_provider: ChatProvider):
        super().__init__()

        self._chat_model = chat_provider

    def add_tool(self, func):
        self._chat_model.add_tool_call(func)

    async def run(self, prompt):
        context = []
        if isinstance(prompt, list):
            context += prompt
        else:
            context = [prompt]

        while True:
            response = await self._chat_model.chat(context)

            if response.tool_calls:
                for i in response.tool_calls:
                    res = i.func(**i.arguments)
                    logger.info(
                        f"Calling tool: {i.name} with args: {i.arguments} got result: {res}"
                    )

                    tool_result = TOOL_CALL_RESULT_PROMPT.format(
                        name=i.name,
                        arguments=json.dumps(i.arguments),
                        result=res,
                    )

                    context.append({"role": "tool", "content": tool_result})

            else:
                return response.response
