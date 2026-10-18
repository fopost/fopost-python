from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

GRAPH = {
    "nodes": [
        {"id": "t", "kind": "trigger", "label": None, "config": {}, "position": 0},
        {"id": "p", "kind": "publish", "label": "Post", "config": {"accounts": ["acc_1"]}},
    ],
    "edges": [{"id": "e1", "source": "t", "source_handle": None, "target": "p"}],
}

AUTOMATION = {
    "id": "auto_1",
    "workspace_id": "ws_1",
    "name": "Cross-post",
    "description": None,
    "trigger_type": "content_created",
    "trigger_config": {"account_id": "acc_1"},
    "active": True,
    "schedule_window": None,
    "max_per_day": None,
    "credit_ceiling": None,
    "approval_mode": False,
    "last_triggered_at": None,
    "run_count": 3,
    "graph": GRAPH,
    "steps": [{"position": 0, "node_id": "p", "action_type": "publish", "action_config": {}}],
    "created_at": "2026-10-18T12:00:00.000Z",
    "updated_at": "2026-10-18T12:00:00.000Z",
}


@respx.mock
def test_crud_toggle_and_stats(client: Fopost) -> None:
    listed = respx.get(f"{BASE_URL}/automations").mock(
        return_value=httpx.Response(200, json={"data": [AUTOMATION]})
    )
    created = respx.post(f"{BASE_URL}/automations").mock(
        return_value=httpx.Response(201, json={**AUTOMATION, "secret": "asec_1"})
    )
    respx.get(f"{BASE_URL}/automations/auto_1").mock(
        return_value=httpx.Response(200, json=AUTOMATION)
    )
    updated = respx.put(f"{BASE_URL}/automations/auto_1").mock(
        return_value=httpx.Response(200, json={**AUTOMATION, "name": "Renamed"})
    )
    deleted = respx.delete(f"{BASE_URL}/automations/auto_1").mock(return_value=httpx.Response(204))
    toggled = respx.post(f"{BASE_URL}/automations/auto_1/toggle").mock(
        return_value=httpx.Response(200, json={"id": "auto_1", "active": False})
    )
    stats = respx.get(f"{BASE_URL}/automations/stats").mock(
        return_value=httpx.Response(
            200,
            json={
                "total_automations": 1,
                "active_automations": 1,
                "total_runs_24h": 2,
                "runs_by_status": {"completed": 2},
                "recent_runs": [
                    {
                        "id": 7,
                        "automation_id": "auto_1",
                        "status": "completed",
                        "started_at": "2026-10-18T12:00:00.000Z",
                        "completed_at": None,
                    }
                ],
            },
        )
    )

    assert [a.id for a in client.automations.list()] == ["auto_1"]
    assert listed.called

    auto = client.automations.create(
        workspace_id="ws_1",
        name="Cross-post",
        trigger_type="content_created",
        trigger_config={"account_id": "acc_1"},
        graph=GRAPH,
    )
    assert auto.secret == "asec_1"
    assert auto.graph is not None and auto.graph.edges[0].target == "p"
    sent = json.loads(created.calls.last.request.content)
    assert sent["workspaceId"] == "ws_1" and sent["triggerType"] == "content_created"
    assert sent["triggerConfig"] == {"account_id": "acc_1"}
    assert sent["graph"]["edges"] == [
        {"id": "e1", "source": "t", "sourceHandle": None, "target": "p"}
    ]

    assert client.automations.get("auto_1").run_count == 3

    renamed = client.automations.update(
        "auto_1", name="Renamed", steps=[{"action_type": "publish", "action_config": {}}]
    )
    assert renamed.name == "Renamed"
    assert json.loads(updated.calls.last.request.content) == {
        "name": "Renamed",
        "steps": [{"actionType": "publish", "actionConfig": {}}],
    }

    client.automations.delete("auto_1")
    assert deleted.called
    assert client.automations.toggle("auto_1").active is False and toggled.called

    totals = client.automations.stats()
    assert stats.called
    assert totals.runs_by_status == {"completed": 2}
    assert totals.recent_runs[0].id == 7


@respx.mock
def test_versions_are_listed_read_and_restored(client: Fopost) -> None:
    listed = respx.get(f"{BASE_URL}/automations/auto_1/versions").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "version": 2,
                        "note": None,
                        "created_by": {"name": "Ops"},
                        "created_at": "2026-10-18T12:00:00.000Z",
                        "node_count": 2,
                        "nodes_added": [{"id": "p", "kind": "publish", "label": "Post"}],
                        "nodes_removed": [],
                    }
                ],
                "meta": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1},
            },
        )
    )
    respx.get(f"{BASE_URL}/automations/auto_1/versions/2").mock(
        return_value=httpx.Response(
            200,
            json={
                "version": 2,
                "note": None,
                "created_by": None,
                "created_at": "2026-10-18T12:00:00.000Z",
                "graph": GRAPH,
            },
        )
    )
    restored = respx.post(f"{BASE_URL}/automations/auto_1/versions/2/restore").mock(
        return_value=httpx.Response(201, json={"version": 3, "graph": GRAPH, "steps": []})
    )

    versions = client.automations.versions("auto_1", page=1, per_page=30)
    assert versions[0].version == 2
    assert versions[0].created_by is not None and versions[0].created_by.name == "Ops"
    assert versions[0].nodes_added[0].kind == "publish"
    assert dict(listed.calls.last.request.url.params) == {"page": "1", "per_page": "30"}

    one = client.automations.get_version("auto_1", 2)
    assert one.graph is not None and [n.id for n in one.graph.nodes] == ["t", "p"]

    result = client.automations.restore_version("auto_1", 2)
    assert restored.called and result.version == 3


@respx.mock
def test_runs_page_and_single_run_with_logs(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/automations/auto_1/runs").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [{"id": 7, "status": "completed", "started_at": "2026-10-18T12:00:00Z"}],
                "meta": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1},
            },
        )
    )
    respx.get(f"{BASE_URL}/automations/auto_1/runs/7").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 7,
                "automation_id": "auto_1",
                "status": "completed",
                "started_at": "2026-10-18T12:00:00Z",
                "logs": [
                    {
                        "id": 1,
                        "step_position": 0,
                        "node_id": "p",
                        "status": "completed",
                        "started_at": "2026-10-18T12:00:00Z",
                        "duration_ms": 40,
                    }
                ],
            },
        )
    )

    runs, meta = client.automations.runs("auto_1")
    assert runs[0].id == 7 and meta.total == 1

    run = client.automations.get_run("auto_1", 7)
    assert run.logs[0].node_id == "p" and run.logs[0].duration_ms == 40
