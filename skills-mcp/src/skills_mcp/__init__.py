from importlib.metadata import version

from skills_mcp.discovery import KNOWN_ROOTS, RootSpec
from skills_mcp.server import build_server, main

__version__ = version("skills-mcp")

__all__ = [
    "KNOWN_ROOTS",
    "RootSpec",
    "__version__",
    "build_server",
    "main",
]
