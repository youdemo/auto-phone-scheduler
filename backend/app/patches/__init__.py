"""Patches module for third-party libraries."""

from app.patches.phone_agent_patch import apply_patches as apply_phone_agent_patches


def apply_all_patches():
    """Apply all patches to third-party libraries."""
    apply_phone_agent_patches()

