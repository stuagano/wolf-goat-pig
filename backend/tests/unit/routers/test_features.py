from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import AppConfig
from app.routers.features import get_features, set_features


def test_stuart_mode_defaults_off_and_can_be_toggled_without_changing_other_flags():
    engine = create_engine("sqlite://")
    AppConfig.__table__.create(engine)
    with Session(engine) as db:
        assert get_features(db)["features"]["stuart_mode"] is False
        db.add(AppConfig(name="features", value={"livsow": True}))
        db.commit()
        enabled = set_features({"stuart_mode": True}, db)["features"]
        assert enabled["stuart_mode"] is True
        assert enabled["livsow"] is True
        disabled = set_features({"stuart_mode": False}, db)["features"]
        assert disabled["stuart_mode"] is False
        assert disabled["livsow"] is True
        assert get_features(db)["features"] == disabled
    engine.dispose()
