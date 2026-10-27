"""Same-day alerts are opt-in, distinct from confirmations, and deduplicated."""

from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.services import same_day_signup_service as service
from app.services.email_service import EmailService


@pytest.fixture
def db(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'alerts.db'}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(service, "SessionLocal", factory)
    session = factory()
    yield session
    session.close()
    engine.dispose()


def player(db, name, *, enabled=True, frequency="daily", active=1):
    profile = models.PlayerProfile(name=name, email=f"{name}@example.com", is_active=active)
    db.add(profile)
    db.flush()
    db.add(
        models.EmailPreferences(
            player_profile_id=profile.id,
            same_day_signups_enabled=enabled,
            signup_confirmations_enabled=False,
            email_frequency=frequency,
        )
    )
    db.flush()
    return profile


def signup(db, profile, *, date="2026-11-01", status="signed_up", time="2026-10-01T10:00:00+00:00"):
    row = models.DailySignup(
        player_profile_id=profile.id,
        player_name=profile.name,
        date=date,
        status=status,
        signup_time=time,
        created_at=time,
        updated_at=time,
    )
    db.add(row)
    db.commit()
    return row


@pytest.fixture
def email(monkeypatch):
    sender = Mock()
    sender.is_configured.return_value = True
    sender.send_same_day_signup_notification.return_value = True
    monkeypatch.setattr(service, "get_email_service", lambda: sender)
    return sender


def test_only_existing_opted_in_players_on_same_date_receive_alert(db, email):
    recipient = player(db, "Alice")
    signup(db, recipient)
    signup(db, player(db, "OptedOut", enabled=False))
    signup(db, player(db, "Paused", frequency="never"))
    signup(db, player(db, "Cancelled"), status="cancelled")
    signup(db, player(db, "OtherDate"), date="2026-11-02")
    signup(db, player(db, "Inactive", active=0))
    no_email = player(db, "NoEmail")
    no_email.email = None
    signup(db, no_email)
    newcomer = player(db, "Bob")
    event = signup(db, newcomer, time="2026-10-01T11:00:00+00:00")
    signup(db, player(db, "Later"), time="2026-10-01T12:00:00+00:00")

    service.deliver_same_day_signup_notifications(event.id)
    service.deliver_same_day_signup_notifications(event.id)

    email.send_same_day_signup_notification.assert_called_once_with(
        to_email=recipient.email,
        player_name="Alice",
        joining_player_name="Bob",
        signup_date="2026-11-01",
        signed_up_count=7,
    )
    assert db.query(models.SameDaySignupNotification).count() == 1


def test_failed_recipient_can_retry_without_resending_successes(db, email):
    signup(db, player(db, "Alice"))
    signup(db, player(db, "Carol"))
    event = signup(db, player(db, "Bob"), time="2026-10-01T11:00:00+00:00")
    email.send_same_day_signup_notification.side_effect = [True, False, True]

    service.deliver_same_day_signup_notifications(event.id)
    service.deliver_same_day_signup_notifications(event.id)

    assert email.send_same_day_signup_notification.call_count == 3
    assert db.query(models.SameDaySignupNotification).count() == 2


def test_admin_signup_delivers_alert_and_keeps_own_confirmation(db, email, monkeypatch):
    from datetime import timedelta

    from app.routers import signup_admin
    from app.utils.time import club_today

    day = (club_today() + timedelta(days=3)).isoformat()
    recipient = player(db, "Alice")
    signup(db, recipient, date=day)
    newcomer = player(db, "Bob")
    newcomer.legacy_name = "Bob"
    db.commit()
    confirmation = Mock()
    monkeypatch.setattr(signup_admin, "_send_signup_confirmation", confirmation)
    monkeypatch.setattr(signup_admin, "get_legacy_signup_service", Mock(return_value=Mock()))
    monkeypatch.setattr(
        signup_admin, "send_same_day_signup_notifications", service.deliver_same_day_signup_notifications
    )

    result = signup_admin.admin_add_signup(
        signup_admin.AdminSignupCreate(date=day, player_profile_id=newcomer.id),
        admin={"email": "admin@example.com"},
        db=db,
    )

    confirmation.assert_called_once_with(result.id, newcomer.email, "Bob", day)
    email.send_same_day_signup_notification.assert_called_once_with(
        to_email=recipient.email,
        player_name="Alice",
        joining_player_name="Bob",
        signup_date=day,
        signed_up_count=2,
    )
    assert db.query(models.SameDaySignupNotification).count() == 1


def test_reactivation_through_update_alerts_existing_players_once(db, email, monkeypatch):
    from app.routers import signups

    bob = player(db, "Bob")
    event = signup(db, bob, status="cancelled", time="2026-09-01T00:00:00+00:00")
    alice = player(db, "Alice")
    signup(db, alice)
    factory = service.SessionLocal
    monkeypatch.setattr(signups.database, "SessionLocal", factory)
    monkeypatch.setattr(signups, "get_legacy_signup_service", Mock(return_value=Mock()))
    monkeypatch.setattr(signups, "send_same_day_signup_notifications", service.deliver_same_day_signup_notifications)
    update = signups.schemas.DailySignupUpdate(status="signed_up")

    signups.update_signup(event.id, update, current_user=bob)
    signups.update_signup(event.id, update, current_user=bob)

    email.send_same_day_signup_notification.assert_called_once_with(
        to_email=alice.email,
        player_name="Alice",
        joining_player_name="Bob",
        signup_date=event.date,
        signed_up_count=2,
    )


def test_existing_sqlite_database_upgrade_preserves_confirmations(tmp_path, monkeypatch):
    from sqlalchemy import inspect, text

    from app import database

    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE email_preferences (id INTEGER PRIMARY KEY, player_profile_id INTEGER, "
                "signup_confirmations_enabled INTEGER DEFAULT 1)"
            )
        )
        connection.execute(text("INSERT INTO email_preferences (id, player_profile_id) VALUES (1, 1)"))
    monkeypatch.setattr(database, "engine", engine)
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine))
    database.init_db()
    database.init_db()
    assert "same_day_signups_enabled" in {column["name"] for column in inspect(engine).get_columns("email_preferences")}
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT signup_confirmations_enabled, same_day_signups_enabled FROM email_preferences WHERE id=1")
        ).one() == (1, 0)
    engine.dispose()


def test_email_content_names_the_joiner_and_date_and_escapes_html(monkeypatch):
    sender = EmailService.__new__(EmailService)
    send = Mock(return_value=True)
    monkeypatch.setattr(sender, "_send_email", send)
    assert sender.send_same_day_signup_notification(
        to_email="alice@example.com",
        player_name="Alice",
        joining_player_name="Bob <script>",
        signup_date="2026-11-01",
        signed_up_count=4,
    )
    address, subject, html_body, text_body = send.call_args.args
    assert address == "alice@example.com"
    assert "2026-11-01" in subject
    assert "Bob &lt;script&gt;" in html_body
    assert "Bob <script>" not in html_body
    assert "2026-11-01" in html_body
    assert "Bob <script>" in text_body
    assert "Manage your email preferences" in text_body
    assert "There are now 4 players signed up." in html_body
    assert "There are now 4 players signed up." in text_body


def test_cancelled_event_and_unconfigured_sender_do_not_send(db, email):
    signup(db, player(db, "Alice"))
    event = signup(db, player(db, "Bob"), status="cancelled")
    service.deliver_same_day_signup_notifications(event.id)
    event.status = "signed_up"
    db.commit()
    email.is_configured.return_value = False
    service.deliver_same_day_signup_notifications(event.id)
    email.send_same_day_signup_notification.assert_not_called()
    assert db.query(models.SameDaySignupNotification).count() == 0
