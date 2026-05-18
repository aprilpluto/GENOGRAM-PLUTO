"""Genogram layout engine — generation-aligned positioning."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from core.models import FamilyGraph, MarriageStatus


class GenogramLayoutEngine:
    """Compute node positions for genogram rendering."""

    NODE_W = 56
    NODE_H = 56
    H_GAP = 100
    V_GAP = 120
    COUPLE_GAP = 24

    def compute(self, graph: FamilyGraph) -> dict[str, Any]:
        generations = self._assign_generations(graph)
        units = self._build_family_units(graph, generations)
        positions: dict[str, dict[str, float]] = {}
        gen_rows: dict[int, list[str]] = defaultdict(list)

        for uid, gen in generations.items():
            gen_rows[gen].append(uid)

        y = 80
        sorted_gens = sorted(gen_rows.keys())

        for gen in sorted_gens:
            row_units = [u for u in units if u["generation"] == gen]
            if not row_units:
                members = gen_rows[gen]
                x = 80
                for pid in members:
                    positions[pid] = {"x": x, "y": y, "generation": gen}
                    x += self.H_GAP + self.NODE_W
            else:
                x = 80
                for unit in row_units:
                    if unit["type"] == "couple":
                        p1, p2 = unit["partners"]
                        positions[p1] = {"x": x, "y": y, "generation": gen}
                        positions[p2] = {
                            "x": x + self.NODE_W + self.COUPLE_GAP,
                            "y": y,
                            "generation": gen,
                        }
                        cx = x + (self.NODE_W * 2 + self.COUPLE_GAP) / 2
                        unit["center_x"] = cx
                        unit["marriage_y"] = y + self.NODE_H / 2
                        x += self.NODE_W * 2 + self.COUPLE_GAP + self.H_GAP
                        child_y = y + self.V_GAP
                        children = unit.get("children", [])
                        child_x_start = cx - (len(children) - 1) * (self.H_GAP + self.NODE_W) / 2
                        for i, cid in enumerate(children):
                            positions[cid] = {
                                "x": child_x_start + i * (self.H_GAP + self.NODE_W),
                                "y": child_y,
                                "generation": gen + 1,
                            }
                    elif unit["type"] == "single":
                        pid = unit["person_id"]
                        positions[pid] = {"x": x, "y": y, "generation": gen}
                        x += self.H_GAP + self.NODE_W
            y += self.V_GAP + self.NODE_H

        links = self._build_links(graph, positions, units)
        bounds = self._compute_bounds(positions)

        return {
            "positions": positions,
            "links": links,
            "units": units,
            "generations": {k: v for k, v in generations.items()},
            "bounds": bounds,
            "config": {
                "nodeWidth": self.NODE_W,
                "nodeHeight": self.NODE_H,
                "hGap": self.H_GAP,
                "vGap": self.V_GAP,
            },
        }

    def _assign_generations(self, graph: FamilyGraph) -> dict[str, int]:
        gen: dict[str, int] = {}
        roots: list[str] = []

        child_set = {link.child_id for link in graph.parent_child_links}
        for pid, person in graph.persons.items():
            role = (person.role_label or "").lower()
            if role in ("ayah", "bapak", "father", "ibu", "mother", "kakek", "nenek"):
                gen[pid] = 0 if role in ("ayah", "bapak", "father", "ibu", "mother") else -1
                roots.append(pid)
            elif pid not in child_set:
                gen.setdefault(pid, 0)

        if not roots:
            for pid in graph.persons:
                gen.setdefault(pid, 0)

        changed = True
        while changed:
            changed = False
            for link in graph.parent_child_links:
                parent_gens = [gen.get(p, 0) for p in link.parent_ids if p in graph.persons]
                if parent_gens:
                    child_gen = max(parent_gens) + 1
                    if gen.get(link.child_id, -1) < child_gen:
                        gen[link.child_id] = child_gen
                        changed = True

        for marriage in graph.marriages.values():
            g1 = gen.get(marriage.partner1_id, 0)
            g2 = gen.get(marriage.partner2_id, 0)
            mg = min(g1, g2)
            gen[marriage.partner1_id] = mg
            gen[marriage.partner2_id] = mg

        for pid in graph.persons:
            gen.setdefault(pid, 0)

        min_gen = min(gen.values()) if gen else 0
        if min_gen < 0:
            offset = -min_gen
            gen = {k: v + offset for k, v in gen.items()}

        return gen

    def _build_family_units(
        self, graph: FamilyGraph, generations: dict[str, int]
    ) -> list[dict[str, Any]]:
        units: list[dict[str, Any]] = []
        used: set[str] = set()

        for marriage in graph.marriages.values():
            p1, p2 = marriage.partner1_id, marriage.partner2_id
            if p1 in used and p2 in used:
                continue
            gen = min(generations.get(p1, 0), generations.get(p2, 0))
            children = list(marriage.children_ids)
            for link in graph.parent_child_links:
                if set(link.parent_ids) <= {p1, p2} and link.child_id not in children:
                    children.append(link.child_id)
            units.append({
                "type": "couple",
                "marriage_id": marriage.id,
                "partners": [p1, p2],
                "status": marriage.status.value,
                "year": marriage.year,
                "divorce_year": marriage.divorce_year,
                "children": children,
                "generation": gen,
            })
            used.update([p1, p2, *children])

        for pid in graph.persons:
            if pid not in used:
                units.append({
                    "type": "single",
                    "person_id": pid,
                    "generation": generations.get(pid, 0),
                })

        units.sort(key=lambda u: (u["generation"], u.get("partners", [u.get("person_id")])[0]))
        return units

    def _build_links(
        self,
        graph: FamilyGraph,
        positions: dict[str, dict],
        units: list[dict],
    ) -> list[dict[str, Any]]:
        links: list[dict[str, Any]] = []

        for unit in units:
            if unit["type"] != "couple":
                continue
            p1, p2 = unit["partners"]
            if p1 not in positions or p2 not in positions:
                continue
            pos1, pos2 = positions[p1], positions[p2]
            x1 = pos1["x"] + self.NODE_W / 2
            x2 = pos2["x"] + self.NODE_W / 2
            y = pos1["y"] + self.NODE_H / 2
            links.append({
                "type": "marriage",
                "status": unit.get("status", "married"),
                "x1": x1, "y1": y, "x2": x2, "y2": y,
                "year": unit.get("year"),
            })
            mid_x = (x1 + x2) / 2
            mid_y = y
            children = unit.get("children", [])
            if children:
                child_ys = [positions[c]["y"] for c in children if c in positions]
                if child_ys:
                    line_y = min(child_ys) - 20
                    links.append({
                        "type": "sibling_bar",
                        "x1": mid_x, "y1": mid_y,
                        "x2": mid_x, "y2": line_y,
                    })
                    child_xs = [
                        positions[c]["x"] + self.NODE_W / 2
                        for c in children if c in positions
                    ]
                    if len(child_xs) > 1:
                        links.append({
                            "type": "sibling_line",
                            "x1": min(child_xs), "y1": line_y,
                            "x2": max(child_xs), "y2": line_y,
                        })
                    for cid in children:
                        if cid not in positions:
                            continue
                        cx = positions[cid]["x"] + self.NODE_W / 2
                        link_type = "child"
                        for pcl in graph.parent_child_links:
                            if pcl.child_id == cid:
                                link_type = pcl.child_type.value
                                break
                        links.append({
                            "type": link_type,
                            "x1": cx, "y1": line_y,
                            "x2": cx, "y2": positions[cid]["y"],
                        })

        return links

    def _compute_bounds(self, positions: dict[str, dict]) -> dict[str, float]:
        if not positions:
            return {"minX": 0, "minY": 0, "maxX": 800, "maxY": 600, "width": 800, "height": 600}
        xs = [p["x"] for p in positions.values()]
        ys = [p["y"] for p in positions.values()]
        pad = 80
        min_x, max_x = min(xs) - pad, max(xs) + self.NODE_W + pad
        min_y, max_y = min(ys) - pad, max(ys) + self.NODE_H + pad
        return {
            "minX": min_x, "minY": min_y,
            "maxX": max_x, "maxY": max_y,
            "width": max_x - min_x,
            "height": max_y - min_y,
        }
