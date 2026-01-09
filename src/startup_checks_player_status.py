from player_status_engine_v11 import (
    _assert_v11,
    V11_PLAYER_STATUS_SIGNATURE,
    PlayerStatus,
    PlayerStatusData,
)

def verify_player_status_engine():
    sig = _assert_v11()
    if sig != V11_PLAYER_STATUS_SIGNATURE:
        raise RuntimeError("❌ Player Status Engine version mismatch")

    # Sanity check: OUT players must always fail
    data = PlayerStatusData(
        player_id="test",
        player_name="Test Player",
        team="TEST",
        injury_status=PlayerStatus.OUT,
    )

    result = evaluate_player_status(data)
    if result.is_eligible:
        raise RuntimeError("❌ OUT player incorrectly marked eligible")
