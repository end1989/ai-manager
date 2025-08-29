"""Adapter modules for external integrations."""

from .llm_stub import LLMStub
from .worker_prompt import WorkerPrompt

__all__ = ["LLMStub", "WorkerPrompt"]