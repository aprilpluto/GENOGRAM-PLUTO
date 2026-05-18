"""AI-inspired natural language parser for family text input."""

from __future__ import annotations

import re
from typing import Any, Optional

from core.models import (
    ChildType,
    FamilyGraph,
    Gender,
    LifeStatus,
    Marriage,
    MarriageStatus,
    ParentChildLink,
    Person,
)


class FamilyTextParser:
    """Parse structured and narrative family text into a FamilyGraph."""

    GENDER_PATTERNS = {
        Gender.MALE: re.compile(
            r"\b(laki[- ]?laki|pria|male|l|boy|bapak|ayah|suami|kakek|paman)\b",
            re.I,
        ),
        Gender.FEMALE: re.compile(
            r"\b(perempuan|wanita|female|p|girl|ibu|istri|nenek|bibi)\b",
            re.I,
        ),
    }

    DECEASED_PATTERN = re.compile(
        r"\b(meninggal|meninggal dunia|almarhum|almarhumah|deceased|dead|wafat|"
        r"telah meninggal|sudah meninggal)\b",
        re.I,
    )

    AGE_PATTERN = re.compile(r"(\d{1,3})\s*tahun", re.I)
    BIRTH_YEAR_PATTERN = re.compile(r"(?:lahir|born)\s*(?:tahun\s*)?(\d{4})", re.I)
    YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")

    ROLE_LINE = re.compile(
        r"^(?:anak\s*(\d+)|child\s*(\d+)|"
        r"(ayah|ibu|bapak|mama|papa|kakek|nenek|suami|istri|"
        r"father|mother|grandfather|grandmother|son|daughter))\s*[:：\-]\s*(.+)$",
        re.I,
    )

    MARRIAGE_LINE = re.compile(
        r"(?:menikah|married|nikah|pernikahan|marriage)\s*(?:dengan|with|kepada)?\s*"
        r"(.+?)(?:\s*,\s*(.+))?$",
        re.I,
    )

    MARRIAGE_YEAR = re.compile(
        r"(?:menikah|married|pernikahan|marriage)\s*(?:tahun|year|thn)?\s*(\d{4})",
        re.I,
    )

    DIVORCE_PATTERN = re.compile(
        r"\b(cerai|divorced|perceraian|bercerai)\b", re.I
    )

    ADOPTION_PATTERN = re.compile(r"\b(adopsi|adopted|adoption|angkat)\b", re.I)
    STEP_PATTERN = re.compile(r"\b(anak tiri|step\s*child|stepchild)\b", re.I)
    TWIN_PATTERN = re.compile(r"\b(kembar|twin|twins)\b", re.I)
    CONFLICT_PATTERN = re.compile(r"\b(konflik|conflict|bertengkar)\b", re.I)

    PERSON_ATTR = re.compile(
        r"^(.+?)\s*,\s*(.+)$"
    )

    def parse(self, text: str) -> tuple[FamilyGraph, list[str], list[dict[str, Any]]]:
        graph = FamilyGraph()
        warnings: list[str] = []
        suggestions: list[dict[str, Any]] = []

        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        pending_parents: list[str] = []
        marriage_year: Optional[int] = None
        child_index = 0

        for i, line in enumerate(lines, 1):
            try:
                if self._parse_marriage_year(line, graph, warnings):
                    my = self.YEAR_PATTERN.search(line)
                    if my:
                        marriage_year = int(my.group(1))
                    self._ensure_parent_marriage(graph, marriage_year)
                    marriage_year = None
                    continue

                if self.DIVORCE_PATTERN.search(line):
                    self._apply_divorce(line, graph, warnings)
                    continue

                role_match = self.ROLE_LINE.match(line)
                if role_match:
                    role = (role_match.group(1) or role_match.group(2) or role_match.group(3))
                    rest = role_match.group(4)
                    person = self._parse_person_attrs(rest)
                    person.role_label = role
                    graph.add_person(person, role=role)
                    if role and role.lower() in ("ayah", "bapak", "father", "ibu", "mother"):
                        pending_parents = [p for p in [graph.role_map.get(role.lower())] if p]
                    if "anak" in (role or "").lower() or role_match.group(1):
                        child_index += 1
                        if len(pending_parents) >= 1:
                            self._link_child(graph, pending_parents, person.id)
                    continue

                marriage_match = self.MARRIAGE_LINE.search(line)
                if marriage_match and "tahun" not in line.lower()[:8]:
                    self._parse_marriage_line(line, graph, warnings, marriage_year)
                    continue

                if re.search(r"\bmenikah\s+dengan\b", line, re.I):
                    line_year = marriage_year
                    y = self.YEAR_PATTERN.search(line)
                    if y:
                        line_year = int(y.group(1))
                    self._parse_named_marriage(line, graph, warnings, line_year)
                    continue

                if re.match(r"^(ayah|ibu)\s*:", line, re.I):
                    parts = line.split(":", 1)
                    role = parts[0].strip().lower()
                    person = self._parse_person_attrs(parts[1])
                    graph.add_person(person, role=role)
                    if role in ("ayah", "ibu", "bapak", "father", "mother"):
                        pending_parents = self._collect_parent_ids(graph)
                    continue

                if re.match(r"^anak\s*\d*\s*:", line, re.I):
                    parts = re.split(r":", line, 1)
                    person = self._parse_person_attrs(parts[1])
                    graph.add_person(person, role=f"anak_{child_index}")
                    child_index += 1
                    parent_ids = self._collect_parent_ids(graph) or self._resolve_parent_ids(graph, pending_parents)
                    if parent_ids:
                        self._link_child(graph, parent_ids, person.id, line)
                    else:
                        warnings.append(
                            f"Baris {i}: Anak '{person.name}' tanpa orang tua terdefinisi."
                        )
                        suggestions.append({
                            "line": i,
                            "type": "missing_parents",
                            "message": f"Tambahkan Ayah/Ibu sebelum anak '{person.name}'.",
                            "fix": f"Ayah: [nama], laki-laki\nIbu: [nama], perempuan",
                        })
                    continue

                person = self._parse_freeform_person(line)
                if person:
                    graph.add_person(person)
            except Exception as exc:
                warnings.append(f"Baris {i}: Gagal parse - {exc}")

        self._ensure_parent_marriage(graph, marriage_year)
        self._infer_missing_genders(graph, warnings, suggestions)
        return graph, warnings, suggestions

    def _collect_parent_ids(self, graph: FamilyGraph) -> list[str]:
        ids = []
        for key in ("ayah", "bapak", "father", "ibu", "mother"):
            pid = graph.role_map.get(key)
            if pid and pid not in ids:
                ids.append(pid)
        return ids

    def _ensure_parent_marriage(
        self, graph: FamilyGraph, year: Optional[int] = None
    ) -> None:
        parent_ids = self._collect_parent_ids(graph)
        if len(parent_ids) < 2:
            return
        p1, p2 = parent_ids[0], parent_ids[1]
        for m in graph.marriages.values():
            if {m.partner1_id, m.partner2_id} == {p1, p2}:
                if year and not m.year:
                    m.year = year
                return
        self._create_marriage(graph, p1, p2, year=year)

    def _parse_person_attrs(self, text: str) -> Person:
        name = text.strip()
        gender = Gender.UNKNOWN
        age = None
        birth_year = None
        life_status = LifeStatus.ALIVE
        conditions: list[str] = []
        child_type = ChildType.BIOLOGICAL

        if self.PERSON_ATTR.match(text):
            parts = [p.strip() for p in text.split(",")]
            name = parts[0]
            for part in parts[1:]:
                gender = self._detect_gender(part) or gender
                age_m = self.AGE_PATTERN.search(part)
                if age_m:
                    age = int(age_m.group(1))
                by = self.BIRTH_YEAR_PATTERN.search(part)
                if by:
                    birth_year = int(by.group(1))
                if self.DECEASED_PATTERN.search(part):
                    life_status = LifeStatus.DECEASED
                if self.ADOPTION_PATTERN.search(part):
                    child_type = ChildType.ADOPTED
                    conditions.append("adopted")
                if self.STEP_PATTERN.search(part):
                    child_type = ChildType.STEP
                    conditions.append("step")
                if self.TWIN_PATTERN.search(part):
                    child_type = ChildType.TWIN
                    conditions.append("twin")
        else:
            gender = self._detect_gender(text) or gender
            age_m = self.AGE_PATTERN.search(text)
            if age_m:
                age = int(age_m.group(1))
            if self.DECEASED_PATTERN.search(text):
                life_status = LifeStatus.DECEASED

        person = Person.create(name=name.split(",")[0].strip(), gender=gender, age=age,
                               birth_year=birth_year, life_status=life_status, conditions=conditions)
        if child_type != ChildType.BIOLOGICAL:
            person.conditions.append(child_type.value)
        return person

    def _parse_freeform_person(self, line: str) -> Optional[Person]:
        if any(kw in line.lower() for kw in ("menikah", "cerai", "tahun 19", "tahun 20")):
            if "menikah" not in line.lower() or "," not in line:
                if not re.search(r"^[A-Za-zÀ-ÿ\s]+,\s*", line):
                    return None
        if ":" in line:
            return None
        if len(line) < 2:
            return None
        return self._parse_person_attrs(line)

    def _detect_gender(self, text: str) -> Optional[Gender]:
        for gender, pattern in self.GENDER_PATTERNS.items():
            if pattern.search(text):
                return gender
        return None

    def _parse_marriage_year(self, line: str, graph: FamilyGraph, warnings: list[str]) -> bool:
        m = self.MARRIAGE_YEAR.search(line) or (
            re.match(r"^menikah\s+tahun\s+(\d{4})$", line, re.I)
        )
        if m:
            return True
        if re.match(r"^menikah\s+tahun\s+\d{4}$", line.strip(), re.I):
            return True
        return bool(re.match(r"^(?:pernikahan|marriage)\s+\d{4}$", line.strip(), re.I))

    def _parse_marriage_line(
        self, line: str, graph: FamilyGraph, warnings: list[str], year: Optional[int]
    ) -> None:
        m = re.search(
            r"(.+?)\s+menikah\s+dengan\s+(.+?)(?:\s*,\s*(.+))?$", line, re.I
        )
        if not m:
            return
        p1 = self._find_or_create(graph, m.group(1).strip())
        p2 = self._parse_person_attrs(m.group(2).strip())
        existing = graph.get_by_role_or_name(p2.name)
        if existing:
            p2 = existing
        else:
            graph.add_person(p2)
        self._create_marriage(graph, p1.id, p2.id, year=year)

    def _parse_named_marriage(
        self, line: str, graph: FamilyGraph, warnings: list[str], year: Optional[int]
    ) -> None:
        m = re.search(r"(.+?)\s+menikah\s+dengan\s+(.+)$", line, re.I)
        if not m:
            return
        left = m.group(1).strip()
        right = m.group(2).strip()
        p1 = graph.get_by_role_or_name(left) or self._parse_person_attrs(left)
        if isinstance(p1, Person) and p1.id not in graph.persons:
            graph.add_person(p1)
        else:
            p1 = graph.get_by_role_or_name(left) or graph.add_person(Person.create(name=left))
        p2 = self._parse_person_attrs(right)
        existing = graph.get_by_role_or_name(p2.name)
        if existing:
            p2 = existing
        else:
            graph.add_person(p2)
        status = MarriageStatus.CONFLICT if self.CONFLICT_PATTERN.search(line) else MarriageStatus.MARRIED
        self._create_marriage(graph, p1.id, p2.id, year=year, status=status)

    def _find_or_create(self, graph: FamilyGraph, identifier: str) -> Person:
        found = graph.get_by_role_or_name(identifier)
        if found:
            return found
        person = self._parse_person_attrs(identifier)
        return graph.add_person(person)

    def _create_marriage(
        self,
        graph: FamilyGraph,
        id1: str,
        id2: str,
        year: Optional[int] = None,
        status: MarriageStatus = MarriageStatus.MARRIED,
    ) -> Marriage:
        import uuid

        marriage = Marriage(
            id=str(uuid.uuid4())[:8],
            partner1_id=id1,
            partner2_id=id2,
            status=status,
            year=year,
        )
        graph.marriages[marriage.id] = marriage
        return marriage

    def _apply_divorce(self, line: str, graph: FamilyGraph, warnings: list[str]) -> None:
        for marriage in graph.marriages.values():
            marriage.status = MarriageStatus.DIVORCED
            y = self.YEAR_PATTERN.search(line)
            if y:
                marriage.divorce_year = int(y.group(1))

    def _resolve_parent_ids(self, graph: FamilyGraph, pending: list[str]) -> list[str]:
        ids = []
        for key in ("ayah", "bapak", "father", "ibu", "mother"):
            pid = graph.role_map.get(key)
            if pid and pid not in ids:
                ids.append(pid)
        if not ids:
            ids = [p for p in pending if p]
        return ids

    def _link_child(
        self,
        graph: FamilyGraph,
        parent_ids: list[str],
        child_id: str,
        line: str = "",
    ) -> None:
        child_type = ChildType.BIOLOGICAL
        if self.ADOPTION_PATTERN.search(line):
            child_type = ChildType.ADOPTED
        elif self.STEP_PATTERN.search(line):
            child_type = ChildType.STEP
        elif self.TWIN_PATTERN.search(line):
            child_type = ChildType.TWIN

        graph.parent_child_links.append(
            ParentChildLink(parent_ids=parent_ids, child_id=child_id, child_type=child_type)
        )
        for mid, marriage in graph.marriages.items():
            if set(parent_ids) <= {marriage.partner1_id, marriage.partner2_id}:
                if child_id not in marriage.children_ids:
                    marriage.children_ids.append(child_id)

    def _infer_missing_genders(
        self,
        graph: FamilyGraph,
        warnings: list[str],
        suggestions: list[dict[str, Any]],
    ) -> None:
        for person in graph.persons.values():
            if person.gender == Gender.UNKNOWN:
                role = (person.role_label or "").lower()
                if role in ("ayah", "bapak", "father", "kakek", "suami"):
                    person.gender = Gender.MALE
                elif role in ("ibu", "mother", "nenek", "istri"):
                    person.gender = Gender.FEMALE
                else:
                    warnings.append(f"Jenis kelamin '{person.name}' tidak jelas — default persegi.")
                    suggestions.append({
                        "type": "ambiguous_gender",
                        "message": f"Tambahkan 'laki-laki' atau 'perempuan' untuk {person.name}.",
                        "person": person.name,
                    })
                    person.gender = Gender.MALE
