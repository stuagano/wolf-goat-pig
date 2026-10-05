from sqlalchemy import create_engine, text

from app import database


def test_existing_sqlite_rounds_survive_submitter_column_upgrade(monkeypatch):
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE legacy_rounds (id INTEGER PRIMARY KEY, member TEXT, status TEXT)"))
        connection.execute(text("INSERT INTO legacy_rounds VALUES (1, 'Existing Player', 'attested')"))
    monkeypatch.setattr(database, "engine", engine)
    database.init_db()
    database.init_db()
    with engine.connect() as connection:
        row = connection.execute(text("SELECT member, submitted_by_profile_id FROM legacy_rounds")).one()
        assert row == ("Existing Player", None)
