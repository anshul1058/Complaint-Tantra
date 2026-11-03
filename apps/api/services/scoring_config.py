"""Editable scoring weights stored in app_settings (admin console, system.md §4.4)."""

from copy import deepcopy

from sqlalchemy.ext.asyncio import AsyncSession

from models import AppSetting

DEFAULTS = {
    "priority": {"criticality": 0.35, "emotion": 0.20, "time": 0.25, "risk": 0.10, "overlap": 0.10},
    "risk": {"load": 0.35, "repeat": 0.25, "web": 0.25, "overlap": 0.15},
    "overlap": {"inst": 0.40, "text": 0.30, "cat": 0.15, "time": 0.15},
}
SETTING_KEY = "scoring_weights"


def _normalise(cfg: dict | None) -> dict:
    out = deepcopy(DEFAULTS)
    for section, values in (cfg or {}).items():
        if section in out and isinstance(values, dict):
            for name, value in values.items():
                if name in out[section]:
                    try:
                        out[section][name] = float(value)
                    except (TypeError, ValueError):
                        pass
    return out


def apply(cfg: dict | None) -> dict:
    """Mutate the modules that own the hot-path constants and return the active config."""
    cfg = _normalise(cfg)
    from services import overlap, priority, risk

    priority.WEIGHTS.update(cfg["priority"])
    risk.RISK_WEIGHTS.update(cfg["risk"])
    overlap.WEIGHTS.update(cfg["overlap"])
    return cfg


async def load(db: AsyncSession) -> dict:
    row = await db.get(AppSetting, SETTING_KEY)
    return apply(row.value if row else None)


async def save(db: AsyncSession, cfg: dict) -> dict:
    cfg = _normalise(cfg)
    row = await db.get(AppSetting, SETTING_KEY)
    if row is None:
        row = AppSetting(key=SETTING_KEY, value=cfg)
        db.add(row)
    else:
        row.value = cfg
    await db.commit()
    return apply(cfg)


if __name__ == "__main__":
    cfg = apply({"priority": {"time": 0.30}, "risk": {"web": 0.30}})
    assert cfg["priority"]["time"] == 0.30 and cfg["priority"]["criticality"] == 0.35
    assert set(cfg) == {"priority", "risk", "overlap"}
    print(cfg)
