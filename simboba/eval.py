"""Eval configuration class for running evaluations."""

from typing import Callable, Any, Optional


class Eval:
    """Configuration for an evaluation.

    Example:
        from simboba import Eval
        from myapp import my_function

        def transform_inputs(messages):
            # Convert generic format to what the function expects
            return {"conversation": messages}

        def transform_output(result):
            # Convert function output to string for judging
            return result["response"]

        my_eval = Eval(
            name="my_agent",
            fn=my_function,
            transform_inputs=transform_inputs,
            transform_output=transform_output,
        )
    """

    def __init__(
        self,
        name: str,
        fn: Callable[..., Any],
        transform_inputs: Optional[Callable[[list], dict]] = None,
        transform_output: Optional[Callable[[Any], str]] = None,
    ):
        self.name = name
        self.fn = fn
        self.transform_inputs = transform_inputs or self._default_transform_inputs
        self.transform_output = transform_output or self._default_transform_output

    def _default_transform_inputs(self, messages: list) -> dict:
        """Default input transformation - pass messages as-is."""
        return {"messages": messages}

    def _default_transform_output(self, result: Any) -> str:
        """Default output transformation - convert to string."""
        return str(result)

    def run(self, messages: list) -> str:
        """Run the evaluation function with the given messages."""
        args = self.transform_inputs(messages)
        result = self.fn(**args)
        return self.transform_output(result)
