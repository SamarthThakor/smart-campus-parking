"""Register domain routes while retaining the existing /api contract."""

from .http import api
from . import security, pages, auth, profile, schedules, parking  # noqa: F401
