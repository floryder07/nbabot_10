from embeds import _assert_v11, V11_SIGNATURE
from projection_engine import _assert_v11 as proj_assert
from parlay_engine_v10_legacy import _assert_v11 as parlay_assert

def verify_v11():
    sig = _assert_v11()
    if sig != V11_SIGNATURE:
        raise RuntimeError("❌ Embed version mismatch detected")
    if proj_assert() != "projection-engine-v10-legacy":
        raise RuntimeError("❌ Projection engine version mismatch")
    if parlay_assert() != "parlay-engine-v10-legacy":
        raise RuntimeError("❌ Parlay engine version mismatch")
