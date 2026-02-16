"""Simboba - Lightweight eval tracking and LLM-as-judge evaluations."""

from simboba.boba import Boba
from simboba.schemas import AgentResponse, MessageInput
from simboba.prompts import JUDGE_PROMPT

__version__ = "0.2.0"
__all__ = ["Boba", "AgentResponse", "MessageInput", "JUDGE_PROMPT"]
