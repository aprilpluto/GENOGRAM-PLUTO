"""Family relationship validation and auto-correction."""

from __future__ import annotations

from typing import Any

from core.models import FamilyGraph, Gender, LifeStatus


class FamilyValidator:
    """Validate genogram structure and suggest corrections."""

    def validate(self, graph: FamilyGraph) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        fixes: list[dict[str, Any]] = []

        if not graph.persons:
            errors.append("Tidak ada anggota keluarga. Tambahkan minimal satu orang.")
            return self._result(errors, warnings, fixes, graph)

        for person in graph.persons.values():
            if not person.name or len(person.name) < 1:
                errors.append(f"Person {person.id} tidak memiliki nama valid.")
            if person.age is not None and (person.age < 0 or person.age > 130):
                warnings.append(f"Usia '{person.name}' ({person.age}) tidak realistis.")
                fixes.append({
                    "type": "age_correction",
                    "person_id": person.id,
                    "suggestion": "Periksa usia — rentang wajar 0–120 tahun.",
                })

        for marriage in graph.marriages.values():
            p1 = graph.persons.get(marriage.partner1_id)
            p2 = graph.persons.get(marriage.partner2_id)
            if not p1 or not p2:
                errors.append(f"Pernikahan {marriage.id}: partner tidak ditemukan.")
                continue
            if p1.gender == p2.gender and p1.gender != Gender.UNKNOWN:
                warnings.append(
                    f"Pernikahan {p1.name} & {p2.name}: jenis kelamin sama — periksa data."
                )

        child_ids = {link.child_id for link in graph.parent_child_links}
        for link in graph.parent_child_links:
            child = graph.persons.get(link.child_id)
            if not child:
                errors.append(f"Anak dengan ID {link.child_id} tidak ditemukan.")
                continue
            valid_parents = [pid for pid in link.parent_ids if pid in graph.persons]
            if len(valid_parents) < 1:
                errors.append(f"Anak '{child.name}' tanpa orang tua valid.")
                fixes.append({
                    "type": "add_parents",
                    "child_id": link.child_id,
                    "suggestion": "Definisikan Ayah dan Ibu sebelum daftar anak.",
                })
            elif len(valid_parents) == 1:
                warnings.append(f"Anak '{child.name}' hanya punya satu orang tua terdefinisi.")
                fixes.append({
                    "type": "single_parent",
                    "child_id": link.child_id,
                    "suggestion": "Tambahkan pasangan orang tua yang hilang.",
                })

        orphans = [
            p for pid, p in graph.persons.items()
            if pid not in child_ids
            and not any(pid in (m.partner1_id, m.partner2_id) for m in graph.marriages.values())
            and len(graph.persons) > 2
        ]
        root_roles = {"ayah", "bapak", "father", "ibu", "mother", "kakek", "nenek"}
        for p in orphans:
            role = (p.role_label or "").lower()
            if role not in root_roles and not any(
                r.person1_id == p.id or r.person2_id == p.id for r in graph.relationships
            ):
                warnings.append(f"'{p.name}' belum terhubung ke struktur keluarga utama.")

        corrected = self._auto_correct(graph, fixes)
        return self._result(errors, warnings, fixes, corrected)

    def _auto_correct(self, graph: FamilyGraph, fixes: list[dict]) -> FamilyGraph:
        for person in graph.persons.values():
            if person.gender == Gender.UNKNOWN:
                role = (person.role_label or "").lower()
                if "ayah" in role or "bapak" in role or "suami" in role:
                    person.gender = Gender.MALE
                elif "ibu" in role or "istri" in role:
                    person.gender = Gender.FEMALE
        return graph

    def _result(
        self,
        errors: list[str],
        warnings: list[str],
        fixes: list[dict],
        graph: FamilyGraph,
    ) -> dict[str, Any]:
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "fixes": fixes,
            "graph": graph.to_dict(),
            "person_count": len(graph.persons),
            "marriage_count": len(graph.marriages),
        }
