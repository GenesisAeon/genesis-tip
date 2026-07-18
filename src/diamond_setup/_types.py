"""Shared type definitions for diamond-setup."""

from typing import TypedDict


class TemplateDict(TypedDict):
    """Structure of a diamond-setup project template."""

    name: str
    description: str
    variables: list[str]
    defaults: dict[str, str]
    files: dict[str, str]
