from app import models
from app.database import SessionLocal, engine


def test_game_state_has_scorecard_image_column():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        g = models.GameStateModel(game_id="img-col-test", game_status="completed", state={}, scorecard_image="data:image/jpeg;base64,AAAA")
        db.add(g)
        db.commit()
        row = db.query(models.GameStateModel).filter_by(game_id="img-col-test").first()
        assert row.scorecard_image == "data:image/jpeg;base64,AAAA"
    finally:
        db.query(models.GameStateModel).filter_by(game_id="img-col-test").delete()
        db.commit()
        db.close()
