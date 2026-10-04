from .interface import AgentBase

from src.llm_providers.interface import ChatProvider

import json
import logging
import uuid

logger = logging.getLogger(__name__)


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

        for _ in range(12):
            response = await self._chat_model.chat(context)

            if response.tool_calls:
                assistant_tool_calls = []
                for call in response.tool_calls:
                    call.call_id = call.call_id or f"call_{uuid.uuid4().hex}"
                    assistant_tool_calls.append(
                        {
                            "id": call.call_id,
                            "type": "function",
                            "function": {
                                "name": call.name,
                                "arguments": json.dumps(call.arguments),
                            },
                        }
                    )
                context.append(
                    {
                        "role": "assistant",
                        "content": response.response,
                        "tool_calls": assistant_tool_calls,
                    }
                )

                for i in response.tool_calls:
                    try:
                        res = i.func(**i.arguments)
                    except Exception as ex:
                        res = json.dumps(
                            {"ok": False, "error": str(ex)}, ensure_ascii=False
                        )
                    logger.info("Called tool %s", i.name)
                    context.append(
                        {
                            "role": "tool",
                            "tool_call_id": i.call_id,
                            "name": i.name,
                            "content": res if isinstance(res, str) else json.dumps(res),
                        }
                    )

            else:
                return response.response

        raise RuntimeError("Agent exceeded the limit of 12 tool-call rounds")
