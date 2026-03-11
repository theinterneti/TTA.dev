"""Unit tests for ProjectSession — Task 6."""

import json


def _manager(tmp_path):
    from ttadev.observability.project_session import ProjectSessionManager

    return ProjectSessionManager(data_dir=tmp_path)


class TestProjectSessionCreate:
    def test_create_persists_json(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("pr-223")
        assert (tmp_path / "projects" / "pr-223.json").exists()
        assert proj.name == "pr-223"
        assert proj.id

    def test_create_sets_created_at(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("feature-x")
        assert proj.created_at

    def test_create_empty_members_and_roles(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("new")
        assert proj.member_agent_ids == []
        assert proj.role_assignments == {}


class TestProjectSessionJoin:
    def test_join_creates_if_missing(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.join("pr-456")
        assert proj.name == "pr-456"
        assert (tmp_path / "projects" / "pr-456.json").exists()

    def test_join_returns_existing(self, tmp_path):
        m = _manager(tmp_path)
        p1 = m.create("existing")
        p2 = m.join("existing")
        assert p1.id == p2.id

    def test_join_idempotent_multiple_times(self, tmp_path):
        m = _manager(tmp_path)
        ids = {m.join("repeated").id for _ in range(3)}
        assert len(ids) == 1


class TestProjectSessionList:
    def test_list_empty(self, tmp_path):
        m = _manager(tmp_path)
        assert m.list() == []

    def test_list_returns_all(self, tmp_path):
        m = _manager(tmp_path)
        m.create("alpha")
        m.create("beta")
        m.create("gamma")
        names = {p.name for p in m.list()}
        assert names == {"alpha", "beta", "gamma"}

    def test_list_newest_first(self, tmp_path):
        import time

        m = _manager(tmp_path)
        m.create("first")
        time.sleep(0.01)
        m.create("second")
        names = [p.name for p in m.list()]
        assert names[0] == "second"


class TestProjectSessionMembership:
    def test_add_member(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("collab")
        m.add_member(proj.id, "agent-aaa")
        updated = m.get(proj.name)
        assert "agent-aaa" in updated.member_agent_ids

    def test_add_member_idempotent(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("collab")
        m.add_member(proj.id, "agent-bbb")
        m.add_member(proj.id, "agent-bbb")
        updated = m.get(proj.name)
        assert updated.member_agent_ids.count("agent-bbb") == 1

    def test_add_multiple_members(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("team")
        m.add_member(proj.id, "agent-1")
        m.add_member(proj.id, "agent-2")
        updated = m.get(proj.name)
        assert set(updated.member_agent_ids) == {"agent-1", "agent-2"}


class TestProjectSessionRoles:
    def test_assign_role(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("review")
        m.assign_role(proj.id, "reviewer", "agent-abc")
        updated = m.get(proj.name)
        assert updated.role_assignments["reviewer"] == "agent-abc"

    def test_assign_multiple_roles(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("dev")
        m.assign_role(proj.id, "implementer", "agent-x")
        m.assign_role(proj.id, "tester", "agent-y")
        updated = m.get(proj.name)
        assert updated.role_assignments["implementer"] == "agent-x"
        assert updated.role_assignments["tester"] == "agent-y"

    def test_reassign_role(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("switch")
        m.assign_role(proj.id, "lead", "agent-old")
        m.assign_role(proj.id, "lead", "agent-new")
        updated = m.get(proj.name)
        assert updated.role_assignments["lead"] == "agent-new"


class TestProjectSessionGet:
    def test_get_existing(self, tmp_path):
        m = _manager(tmp_path)
        m.create("findme")
        proj = m.get("findme")
        assert proj is not None
        assert proj.name == "findme"

    def test_get_missing_returns_none(self, tmp_path):
        m = _manager(tmp_path)
        assert m.get("ghost") is None

    def test_roundtrip_json(self, tmp_path):
        m = _manager(tmp_path)
        proj = m.create("roundtrip")
        m.add_member(proj.id, "agent-z")
        m.assign_role(proj.id, "owner", "agent-z")
        # Re-read from disk
        data = json.loads((tmp_path / "projects" / "roundtrip.json").read_text())
        assert data["name"] == "roundtrip"
        assert "agent-z" in data["member_agent_ids"]
        assert data["role_assignments"]["owner"] == "agent-z"
