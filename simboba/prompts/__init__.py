"""Prompt templates for simboba."""

from simboba.prompts.generation import (
    DATASET_GENERATION_PROMPT,
    GENERATION_PROMPT,
    GENERATION_PROMPT_WITH_FILES,
    build_dataset_generation_prompt,
    build_generation_prompt,
    build_generation_prompt_with_files,
)
from simboba.prompts.judge import (
    JUDGE_PROMPT,
    build_judge_prompt,
    format_conversation,
)

__all__ = [
    "DATASET_GENERATION_PROMPT",
    "GENERATION_PROMPT",
    "GENERATION_PROMPT_WITH_FILES",
    "build_dataset_generation_prompt",
    "build_generation_prompt",
    "build_generation_prompt_with_files",
    "JUDGE_PROMPT",
    "build_judge_prompt",
    "format_conversation",
]
