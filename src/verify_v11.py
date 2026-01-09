"""
NBABot v11 — Central Engine Verification Gate

FAILS FAST if any core engine is not v11-compatible.
"""

# ============================================
# EMBEDS ENGINE
# ============================================
from embeds import _assert_v11 as embeds_assert, V11_SIGNATURE


# ============================================
# PLAYER STATUS ENGINE
# ============================================
from player_status_engine_v11 import (
    _assert_v11 as status_assert,
    V11_PLAYER_STATUS_SIGNATURE
)


def verify_v11() -> None:
    """
    Verify all v11-locked engines.
    Hard stop on ANY mismatch.
    """
    checks = [
        ("Embeds", embeds_assert, V11_SIGNATURE),
        ("Player Status", status_assert, V11_PLAYER_STATUS_SIGNATURE),
    ]

    for name, assert_fn, expected_sig in checks:
        actual = assert_fn()
        if actual != expected_sig:
            raise RuntimeError(
                f"❌ {name} engine version mismatch "
                f"(expected {expected_sig}, got {actual})"
            )

    print("✅ All v11 engines verified")
