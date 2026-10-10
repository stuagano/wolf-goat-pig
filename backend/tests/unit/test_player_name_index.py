from types import SimpleNamespace

from app.services.player_name_index import profile_id_for_member, profile_ids_by_member


class _Query:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _Db:
    def __init__(self, rows):
        self._rows = rows

    def query(self, *_columns):
        return _Query(self._rows)


def test_legacy_name_wins_and_display_name_fills_the_gap():
    rows = [
        (7, "Stu Gano", "Stuart Gano"),
        (8, "Coulburn", None),
    ]
    index = profile_ids_by_member(_Db(rows))
    assert profile_id_for_member("stuart gano", index) == 7
    assert profile_id_for_member("Stu Gano", index) is None
    assert profile_id_for_member("coulburn", index) == 8


def test_two_profiles_sharing_a_name_stay_unlinked():
    rows = [
        (1, "Pat Lee", None),
        (2, "Pat Lee", None),
    ]
    index = profile_ids_by_member(_Db(rows))
    assert profile_id_for_member("Pat Lee", index) is None


def test_lookup_ignores_blank_names():
    index = profile_ids_by_member(_Db([(3, "  ", None)]))
    assert profile_id_for_member(None, index) is None
    assert profile_id_for_member("   ", index) is None
    assert isinstance(SimpleNamespace(id=3), SimpleNamespace)
