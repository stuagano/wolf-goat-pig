"""Unit test for SheetIntegrationService transaction isolation.

Regression (salvaged from root tests/integration/test_sheet_sync_fix.py):
a single bad row (blank player name) must not abort the whole sheet sync —
valid players on either side of the bad row still persist (per-row savepoints).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, PlayerProfile
from app.services.sheet_integration_service import SheetIntegrationService

TEST_DATABASE_URL = "sqlite:///./test_sheet_integration.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_one_bad_row_does_not_abort_the_sync(db):
    sheet_data = [
        {
            "Player Name": "Sync Player 1",
            "Games Played": "10",
            "Games Won": "5",
            "Total Earnings": "$100.00",
        },
        {
            "Player Name": "",  # blank name -> real row-level error path (savepoint rollback)
            "Games Played": "3",
            "Games Won": "1",
            "Total Earnings": "$50.00",
        },
        {
            "Player Name": "Sync Player 3",
            "Games Played": "15",
            "Games Won": "8",
            "Total Earnings": "$200.00",
        },
    ]

    service = SheetIntegrationService(db)
    mappings = service.create_column_mappings(list(sheet_data[0].keys()))
    results = service.sync_sheet_data_to_database(sheet_data, mappings)

    # The bad row is reported, not swallowed silently...
    assert len(results["errors"]) >= 1
    # ...and the two valid players on either side of it still persist.
    assert db.query(PlayerProfile).filter_by(name="Sync Player 1").first() is not None
    assert db.query(PlayerProfile).filter_by(name="Sync Player 3").first() is not None
