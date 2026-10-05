from .interface import AgentBase

from src.llm_providers.interface import ChatProvider

import json
import logging
import uuid
from copy import deepcopy
from time import perf_counter

logger = logging.getLogger(__name__)


class FormattingFailuresExhausted(RuntimeError):
    """Raised when a paper keeps producing malformed or schema-invalid tool input."""


class SimpleAgnet(AgentBase):
    def __init__(self, chat_provider: ChatProvider):
        super().__init__()

        self._chat_model = chat_provider

    def add_tool(self, func):
        self._chat_model.add_tool_call(func)

    async def run(self, prompt, *, recover_formatting: bool = False):
        context = []
        if isinstance(prompt, list):
            context += prompt
        else:
            context = [prompt]
        original_context = deepcopy(context)
        formatting_failures = 0

        def record_formatting_failure(message: str) -> None:
            nonlocal context, formatting_failures
            formatting_failures += 1
            logger.warning(
                "Formatting failure %d/13: %s",
                formatting_failures,
                message,
            )
            if formatting_failures >= 13:
                raise FormattingFailuresExhausted(
                    "Thirteen malformed or schema-invalid responses"
                )

            if formatting_failures == 4:
                context = deepcopy(original_context)
                logger.warning(
                    "Cleared repair conversation after fourth formatting failure"
                )
            context.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous structured response failed formatting or schema "
                        "validation. Rebuild the complete tool arguments carefully and "
                        "follow the tool schema. Do not repeat the malformed response. "
                        f"Failure {formatting_failures}/13: {message}"
                    ),
                }
            )

        for _ in range(12 + (13 if recover_formatting else 0)):
            try:
                response = await self._chat_model.chat(context)
            except json.JSONDecodeError as ex:
                if not recover_formatting:
                    raise
                record_formatting_failure(
                    f"LLM tool-call arguments were not valid JSON: {ex.msg}"
                )
                continue

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

                formatting_errors = []
                for i in response.tool_calls:
                    started = perf_counter()
                    logger.info("Starting tool %s call_id=%s", i.name, i.call_id)
                    try:
                        res = i.func(**i.arguments)
                    except Exception as ex:
                        logger.exception(
                            "Tool %s failed call_id=%s elapsed=%.3fs",
                            i.name, i.call_id, perf_counter() - started,
                        )
                        res = json.dumps(
                            {"ok": False, "error": str(ex)}, ensure_ascii=False
                        )
                        if (
                            recover_formatting
                            and i.name == "add_perovskite_structure"
                            and isinstance(ex, ValueError)
                            and "Document does not match PerovskiteData" in str(ex)
                        ):
                            formatting_errors.append(str(ex))
                    else:
                        logger.info(
                            "Tool %s returned call_id=%s elapsed=%.3fs",
                            i.name, i.call_id, perf_counter() - started,
                        )
                    context.append(
                        {
                            "role": "tool",
                            "tool_call_id": i.call_id,
                            "name": i.name,
                            "content": res if isinstance(res, str) else json.dumps(res),
                        }
                    )
                for message in formatting_errors:
                    record_formatting_failure(message)

            else:
                return response.response

        raise RuntimeError("Agent exceeded the limit of 12 tool-call rounds")
