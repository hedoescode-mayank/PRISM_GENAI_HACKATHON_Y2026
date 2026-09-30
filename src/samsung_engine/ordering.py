"""Internal action dependency graph; never serializes internal metadata."""

from __future__ import annotations

from dataclasses import dataclass, field

from .schema import Action, ActionCategory


class OrderingError(ValueError):
    pass


@dataclass(frozen=True)
class ActionNode:
    id: str
    action: Action
    depends_on: frozenset[str] = field(default_factory=frozenset)
    disruptiveness: int = 0
    reversible: bool = True


def order_actions(nodes: list[ActionNode]) -> list[Action]:
    by_id = {node.id: node for node in nodes}
    if len(by_id) != len(nodes):
        raise OrderingError("duplicate action IDs")
    if len({node.action.actionName.casefold() for node in nodes}) != len(nodes):
        raise OrderingError("duplicate action names")
    dependencies = {node.id: set(node.depends_on) for node in nodes}
    for node in nodes:
        missing = dependencies[node.id] - by_id.keys()
        if missing:
            raise OrderingError(f"unknown dependencies for {node.id}: {sorted(missing)}")
        if node.id in dependencies[node.id]:
            raise OrderingError("self dependency")
        if node.action.category == ActionCategory.critical:
            continue
        # PDF requires every critical operation after noncritical work.
        for critical in nodes:
            if critical.action.category == ActionCategory.critical:
                dependencies[critical.id].add(node.id)
    output: list[Action] = []
    ready = {node.id for node in nodes if not dependencies[node.id]}
    while ready:
        chosen = min(ready, key=lambda key: (
            by_id[key].action.category == ActionCategory.critical,
            by_id[key].disruptiveness,
            not by_id[key].reversible,
            key,
        ))
        ready.remove(chosen)
        output.append(by_id[chosen].action)
        for other in dependencies:
            dependencies[other].discard(chosen)
        emitted = {action.actionName.casefold() for action in output}
        ready.update(key for key, node in by_id.items() if not dependencies[key] and node.action.actionName.casefold() not in emitted)
    if len(output) != len(nodes):
        raise OrderingError("action dependency cycle or critical ordering conflict")
    return output
