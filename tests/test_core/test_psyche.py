import pytest
from src.psyche.core.engine import PsycheEngine
from src.config.settings.settings import settings


@pytest.fixture
def psyche_engine(tmp_path):
    """创建独立 PsycheEngine 实例用于测试（使用临时状态文件，避免污染全局）。"""
    state_path = tmp_path / "psyche_state_test.json"
    return PsycheEngine(state_file_path=str(state_path))


def test_update_state_clamps_values(psyche_engine):
    """验证状态值始终在 0.0-1.0 之间"""
    engine = psyche_engine
    engine.update_state({"fear": 10.0, "curiosity": -5.0})
    state = engine.get_raw_state()
    assert 0.0 <= state["dimensions"]["fear"]["value"] <= 1.0
    assert 0.0 <= state["dimensions"]["curiosity"]["value"] <= 1.0


def test_decay_toward_baseline(psyche_engine):
    """验证每次更新后值会向 baseline 回归"""
    engine = psyche_engine

    engine.update_state({"fear": 0.5})
    state1 = engine.get_raw_state()
    fear1 = state1["dimensions"]["fear"]["value"]
    baseline = state1["dimensions"]["fear"]["baseline"]

    engine.update_state({})
    state2 = engine.get_raw_state()
    fear2 = state2["dimensions"]["fear"]["value"]

    assert abs(fear2 - baseline) < abs(fear1 - baseline)


def test_sensitivity_affects_change(psyche_engine):
    """验证 sensitivity 系数对刺激增量生效（考虑 decay 的存在）。"""
    engine = psyche_engine

    raw = engine.get_raw_state()
    raw["dimensions"]["fear"]["sensitivity"] = 2.0
    engine.state = raw

    v0 = engine.get_raw_state()["dimensions"]["fear"]["value"]
    baseline = engine.get_raw_state()["dimensions"]["fear"]["baseline"]
    decay_rate = settings.PSYCHE_DECAY_RATE

    engine.update_state({"fear": 0.1})
    v1 = engine.get_raw_state()["dimensions"]["fear"]["value"]

    # 期望路径：先刺激再衰减
    expected_after_stimulus = max(0.0, min(1.0, v0 + 0.1 * 2.0))
    expected_after_decay = expected_after_stimulus + (baseline - expected_after_stimulus) * decay_rate

    assert v1 == pytest.approx(expected_after_decay, rel=1e-6, abs=1e-6)
