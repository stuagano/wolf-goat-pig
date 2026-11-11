"""Nightly round-story bell prompts + the weekly email's "From the round stories" section."""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Notification, PlayerProfile, RoundComment, RoundReaction
from app.services import story_prompts, weekly_highlights
from app.services.email_service import EmailService
from app.services.unified_data_service import UnifiedRound

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Wed 2026-10-14 04:00 UTC = Tue 9pm PDT, so "today" (Pacific) is 2026-10-13.
NIGHT = datetime(2026, 10, 14, 4, 0)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()
        Base.metadata.drop_all(bind=engine)


def player(db, name, **kw):
    p = PlayerProfile(name=name, is_active=kw.get("active", 1), is_ai=0, created_at="2026-01-01T00:00:00")
    db.add(p)
    db.commit()
    return p


def rnd(member, day, *, group="A", location="Wing Point", game_id=None, player_id=None):
    return UnifiedRound(
        date=datetime.strptime(day, "%Y-%m-%d").strftime("%d-%b").lstrip("0"),
        date_sortable=day,
        group=group,
        member=member,
        score=4.0,
        location=location,
        game_id=game_id,
        player_id=player_id,
    )


@pytest.fixture
def season(monkeypatch):
    rounds = []

    class Fake:
        def get_season_rounds(self):
            return rounds

    for mod in (story_prompts, weekly_highlights):
        monkeypatch.setattr(mod, "get_unified_data_service", lambda db=None: Fake())
    return rounds


def prompts(db):
    return db.query(Notification).filter(Notification.notification_type == "story_prompt").all()


class TestStoryPrompts:
    def test_prompts_each_linked_player_once_per_recent_round(self, db, season):
        ann, bob, _inactive = player(db, "Ann"), player(db, "Bob"), player(db, "Gone", active=0)
        season += [
            rnd("Ann", "2026-10-13"),
            rnd("Bob", "2026-10-13", game_id="g-1", player_id=bob.id),
            rnd("Gone", "2026-10-13"),  # inactive: nobody watching the bell
            rnd("Guest McGuest", "2026-10-13"),  # no profile
            rnd("Ann", "2026-10-01"),  # outside the lookback
        ]

        assert story_prompts.run(db, now=NIGHT)["prompted"] == 2
        by_player = {n.player_profile_id: n for n in prompts(db)}
        assert set(by_player) == {ann.id, bob.id}
        assert by_player[ann.id].data["path"] == "/rounds/2026-10-13/A?location=Wing%20Point"
        assert by_player[bob.id].data["path"] == "/game/g-1"
        assert "Check the scores and add a story" in by_player[ann.id].message

        # Rerun (and overlapping lookback) never double-prompts, even once read.
        for n in prompts(db):
            n.is_read = True
        db.commit()
        assert story_prompts.run(db, now=NIGHT)["prompted"] == 0
        assert len(prompts(db)) == 2

    def test_dry_run_creates_nothing(self, db, season):
        player(db, "Ann")
        season.append(rnd("Ann", "2026-10-13"))
        assert story_prompts.run(db, now=NIGHT, dry_run=True)["prompted"] == 1
        assert prompts(db) == []


def comment(db, author, body, *, game_id=None, date="2026-10-13", group="A", location="Wing Point", at="2026-10-14"):
    c = RoundComment(
        game_id=game_id,
        round_date=date,
        round_group=group,
        location=location,
        author_profile_id=author.id,
        body=body,
        created_at=f"{at}T00:00:00",
    )
    db.add(c)
    db.commit()
    return c


def react(db, c, who, emoji="😂"):
    db.add(
        RoundReaction(
            round_date=c.round_date,
            round_group=c.round_group,
            location=c.location,
            comment_id=c.id,
            profile_id=who.id,
            emoji=emoji,
            created_at="2026-10-14T00:00:00",
        )
    )
    db.commit()


class TestTopStories:
    def test_matches_week_rounds_and_ranks_by_reactions(self, db, season):
        ann, bob, cy = player(db, "Ann"), player(db, "Bob"), player(db, "Cy")
        week = [rnd("Ann", "2026-10-13"), rnd("Bob", "2026-10-11", group="B", game_id="g-9")]
        quiet = comment(db, ann, "Quiet one", at="2026-10-15")
        funny = comment(db, bob, "Bob found the pond twice", date="13-Oct")  # sheet-form date
        app = comment(db, cy, "Lone wolf on 7!", game_id="g-9", date="2026-10-11", group="B")
        comment(db, ann, "Other week", date="2026-09-01")
        for who in (ann, cy):
            react(db, funny, who)
        react(db, app, ann)

        stories = weekly_highlights.top_stories(db, week)

        assert [s["body"] for s in stories] == [funny.body, app.body, quiet.body]
        assert stories[0] == {
            "author": "Bob",
            "body": funny.body,
            "where": "13-Oct at Wing Point",
            "path": "/rounds/2026-10-13/A?location=Wing%20Point",
            "reactions": 2,
        }
        assert stories[1]["path"] == "/game/g-9"

    def test_none_when_no_comments(self, db, season):
        assert weekly_highlights.top_stories(db, [rnd("Ann", "2026-10-13")]) == []


class TestEmailStories:
    def _render(self, monkeypatch, stories):
        sent = {}
        svc = EmailService.__new__(EmailService)
        monkeypatch.setattr(svc, "_get_base_template", lambda: "{{ content }}", raising=False)
        monkeypatch.setattr(svc, "_send_email", lambda **kw: sent.update(kw) or True, raising=False)
        monkeypatch.setattr(svc, "_preferences_url", lambda: "https://x/account", raising=False)
        monkeypatch.setattr(svc, "_intro_html", lambda intro: "", raising=False)
        highlights = {"rounds": 1, "courses": ["Wing Point"], "players": ["Ann"], "stories": stories}
        assert svc.send_weekly_highlights(to_email="a@x", player_name="Ann", highlights=highlights)
        return sent

    def test_stories_rendered_and_escaped(self, monkeypatch):
        monkeypatch.setenv("FRONTEND_URL", "https://wgp.example")
        story = {"author": "Bob", "body": "<b>pond</b> twice", "where": "13-Oct", "path": "/game/g-1", "reactions": 2}
        sent = self._render(monkeypatch, [story])
        assert "From the round stories" in sent["html_body"]
        assert "&lt;b&gt;pond&lt;/b&gt; twice" in sent["html_body"]
        assert 'href="https://wgp.example/game/g-1"' in sent["html_body"]
        assert '"<b>pond</b> twice" (Bob, 13-Oct) https://wgp.example/game/g-1' in sent["text_body"]

    def test_section_omitted_without_stories(self, monkeypatch):
        sent = self._render(monkeypatch, [])
        for fmt in ("html_body", "text_body"):
            assert "From the round stories" not in sent[fmt]
            # No incomplete rounds: no coverage line, and never the appearance counts.
            assert "incomplete" not in sent[fmt]
            assert "appearances" not in sent[fmt]
