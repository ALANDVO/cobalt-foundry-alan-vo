"""Domain-specific exceptions."""


class SkillDiscoveryError(Exception):
    """Raised when the repository path cannot be discovered or indexed."""


class SkillParseError(Exception):
    """Raised when a SKILL.md file cannot be parsed."""


class SearchError(Exception):
    """Raised when search cannot be performed (e.g., index empty)."""