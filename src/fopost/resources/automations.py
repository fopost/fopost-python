"""``client.automations`` — trigger → pipeline workflows, their versions and runs."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import Any

from .._http import unwrap
from ..models import (
    Automation,
    AutomationPageMeta,
    AutomationRestoredVersion,
    AutomationRun,
    AutomationRunSummary,
    AutomationStats,
    AutomationToggle,
    AutomationVersion,
)
from ._base import UNSET, Resource, drop_unset, parse_list

__all__ = ["AutomationsResource"]


def _camel_graph(graph: Mapping[str, Any]) -> dict[str, Any]:
    """The write side spells ``sourceHandle`` in camelCase; accept either."""
    edges = []
    for edge in graph.get("edges", []):
        edge = dict(edge)
        if "source_handle" in edge:
            edge["sourceHandle"] = edge.pop("source_handle")
        edges.append(edge)
    return {**dict(graph), "edges": edges}


def _camel_steps(steps: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for step in steps:
        step = dict(step)
        if "action_type" in step:
            step["actionType"] = step.pop("action_type")
        if "action_config" in step:
            step["actionConfig"] = step.pop("action_config")
        out.append(step)
    return out


class AutomationsResource(Resource):
    def list(self) -> builtins.list[Automation]:
        return parse_list(Automation, unwrap(self._http.get("/automations")))

    def create(
        self,
        *,
        workspace_id: str,
        name: str,
        trigger_type: str,
        description: str | None = None,
        trigger_config: Mapping[str, Any] | None = None,
        steps: Sequence[Mapping[str, Any]] | None = None,
        graph: Mapping[str, Any] | None = None,
        active: bool | None = None,
    ) -> Automation:
        """Create a workflow. The webhook trigger ``secret`` comes back only here.

        ``steps`` are ``{"action_type": ..., "action_config": {...}}`` dicts and
        ``graph`` is ``{"nodes": [...], "edges": [...]}``; pass one or the other.
        """
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "name": name,
            "triggerType": trigger_type,
        }
        optional: dict[str, Any] = {
            "description": description,
            "triggerConfig": dict(trigger_config) if trigger_config is not None else None,
            "steps": _camel_steps(steps) if steps is not None else None,
            "graph": _camel_graph(graph) if graph is not None else None,
            "active": active,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        return Automation.model_validate(unwrap(self._http.post("/automations", body)))

    def get(self, automation_id: str) -> Automation:
        return Automation.model_validate(unwrap(self._http.get(f"/automations/{automation_id}")))

    def update(
        self,
        automation_id: str,
        *,
        name: str | Any = UNSET,
        description: str | None | Any = UNSET,
        trigger_type: str | Any = UNSET,
        trigger_config: Mapping[str, Any] | Any = UNSET,
        steps: Sequence[Mapping[str, Any]] | Any = UNSET,
        graph: Mapping[str, Any] | Any = UNSET,
        active: bool | Any = UNSET,
    ) -> Automation:
        """Partial update. Passing ``graph`` or ``steps`` replaces the whole graph."""
        body = drop_unset(
            {
                "name": name,
                "description": description,
                "triggerType": trigger_type,
                "triggerConfig": dict(trigger_config) if trigger_config is not UNSET else UNSET,
                "steps": _camel_steps(steps) if steps is not UNSET else UNSET,
                "graph": _camel_graph(graph) if graph is not UNSET else UNSET,
                "active": active,
            }
        )
        return Automation.model_validate(
            unwrap(self._http.put(f"/automations/{automation_id}", body))
        )

    def delete(self, automation_id: str) -> None:
        self._http.delete(f"/automations/{automation_id}")

    def toggle(self, automation_id: str) -> AutomationToggle:
        """Flip the automation on or off."""
        return AutomationToggle.model_validate(
            unwrap(self._http.post(f"/automations/{automation_id}/toggle"))
        )

    def stats(self) -> AutomationStats:
        """Totals, run counts by status for the last 24 hours, and the 10 latest runs."""
        return AutomationStats.model_validate(unwrap(self._http.get("/automations/stats")))

    def versions(
        self, automation_id: str, *, page: int = 1, per_page: int = 30
    ) -> builtins.list[AutomationVersion]:
        """Every saved graph, newest first, with what each save added and removed."""
        body = self._http.get(
            f"/automations/{automation_id}/versions", {"page": page, "per_page": per_page}
        )
        return parse_list(AutomationVersion, unwrap(body))

    def get_version(self, automation_id: str, version: int) -> AutomationVersion:
        """The graph as it was saved at that version."""
        return AutomationVersion.model_validate(
            unwrap(self._http.get(f"/automations/{automation_id}/versions/{version}"))
        )

    def restore_version(self, automation_id: str, version: int) -> AutomationRestoredVersion:
        """Save that version's graph as a new version on top of the history."""
        return AutomationRestoredVersion.model_validate(
            unwrap(self._http.post(f"/automations/{automation_id}/versions/{version}/restore"))
        )

    def runs(
        self, automation_id: str, *, page: int = 1, per_page: int = 30
    ) -> tuple[builtins.list[AutomationRunSummary], AutomationPageMeta]:
        """One page of runs plus its meta."""
        body = self._http.get(
            f"/automations/{automation_id}/runs", {"page": page, "per_page": per_page}
        )
        items = parse_list(AutomationRunSummary, unwrap(body))
        raw_meta = body.get("meta") if isinstance(body, dict) else None
        meta = (
            AutomationPageMeta.model_validate(raw_meta)
            if isinstance(raw_meta, dict)
            else AutomationPageMeta()
        )
        return items, meta

    def get_run(self, automation_id: str, run_id: int) -> AutomationRun:
        """One run with its per-step execution logs."""
        return AutomationRun.model_validate(
            unwrap(self._http.get(f"/automations/{automation_id}/runs/{run_id}"))
        )
