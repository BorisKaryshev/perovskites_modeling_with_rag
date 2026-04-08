from enum import Enum
from typing import List, Union, Optional
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class Metric:
    name: str
    available_values: List[Union[str, int, bool]]
    prompt: str
    is_boolean: bool = False

    _response_type: Optional[type] = None
    _format_prompt: Optional[str] = None

    def compile_prompt(self, **kwargs):
        return self.prompt.format(
            name=self.name,
            available_values=self.available_values,
            **kwargs,
        )

    def get_response_class(self) -> type:
        if self._response_type is not None:
            return self._response_type

        ValidVerdict = Enum(
            "ValidVerdict",
            ((str(i), i) for i in self.available_values),
            type=str,
        )

        class ModelResponse(BaseModel):
            is_boolean: bool = self.is_boolean

            metric_name: str = self.name
            verdict: ValidVerdict

            @property
            def parsed_verdict(self):
                if self.is_boolean:
                    return str(self.verdict.value).lower() in ("1", "true")
                return self.verdict.value

        self._response_type = ModelResponse
        return self._response_type

    def get_output_format_prompt(self):
        if self._format_prompt is not None:
            return self._format_prompt

        examples_of_complete_output = "\n".join(
            [
                self.get_response_class()(name=self.name, verdict=i).model_dump_json()
                for i in self.available_values
            ]
        )

        self._format_prompt = f"""
You must return output in following pydantic format:
{self.get_response_class().model_json_schema()}

Examples:
{examples_of_complete_output}
"""
        return self._format_prompt
