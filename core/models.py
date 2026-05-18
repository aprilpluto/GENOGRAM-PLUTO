"""Domain models for genogram family structure."""



from __future__ import annotations



from dataclasses import dataclass, field, asdict

from enum import Enum

from typing import Any, Optional

import uuid





class Gender(str, Enum):

    MALE = "male"

    FEMALE = "female"

    UNKNOWN = "unknown"





class LifeStatus(str, Enum):

    ALIVE = "alive"

    DECEASED = "deceased"

    UNKNOWN = "unknown"





class MarriageStatus(str, Enum):

    MARRIED = "married"

    DIVORCED = "divorced"

    SEPARATED = "separated"

    ENGAGED = "engaged"

    WIDOWED = "widowed"

    PARTNER = "partner"

    CONFLICT = "conflict"

    CLOSE = "close"

    DISTANT = "distant"





class ChildType(str, Enum):

    BIOLOGICAL = "biological"

    ADOPTED = "adopted"

    FOSTER = "foster"

    STEP = "step"

    TWIN = "twin"

    IDENTICAL_TWIN = "identical_twin"





@dataclass

class Person:

    id: str

    name: str

    gender: Gender = Gender.UNKNOWN

    age: Optional[int] = None

    birth_year: Optional[int] = None

    birth_date: Optional[str] = None

    life_status: LifeStatus = LifeStatus.ALIVE

    role_label: Optional[str] = None

    notes: str = ""

    conditions: list[str] = field(default_factory=list)



    @staticmethod

    def create(name: str, **kwargs: Any) -> "Person":

        return Person(id=str(uuid.uuid4())[:8], name=name.strip(), **kwargs)



    def to_dict(self) -> dict[str, Any]:

        d = asdict(self)

        d["gender"] = self.gender.value

        d["life_status"] = self.life_status.value

        return d



    @classmethod

    def from_dict(cls, data: dict[str, Any]) -> "Person":

        return cls(

            id=data.get("id", str(uuid.uuid4())[:8]),

            name=data.get("name", "Unknown"),

            gender=Gender(data.get("gender", "unknown")),

            age=data.get("age"),

            birth_year=data.get("birth_year"),

            birth_date=data.get("birth_date"),

            life_status=LifeStatus(data.get("life_status", "alive")),

            role_label=data.get("role_label"),

            notes=data.get("notes", ""),

            conditions=data.get("conditions", []),

        )





@dataclass

class Marriage:

    id: str

    partner1_id: str

    partner2_id: str

    status: MarriageStatus = MarriageStatus.MARRIED

    year: Optional[int] = None

    divorce_year: Optional[int] = None

    children_ids: list[str] = field(default_factory=list)



    def to_dict(self) -> dict[str, Any]:

        d = asdict(self)

        d["status"] = self.status.value

        return d



    @classmethod

    def from_dict(cls, data: dict[str, Any]) -> "Marriage":

        return cls(

            id=data.get("id", str(uuid.uuid4())[:8]),

            partner1_id=data["partner1_id"],

            partner2_id=data["partner2_id"],

            status=MarriageStatus(data.get("status", "married")),

            year=data.get("year"),

            divorce_year=data.get("divorce_year"),

            children_ids=data.get("children_ids", []),

        )





@dataclass

class ParentChildLink:

    parent_ids: list[str]

    child_id: str

    child_type: ChildType = ChildType.BIOLOGICAL



    def to_dict(self) -> dict[str, Any]:

        return {

            "parent_ids": self.parent_ids,

            "child_id": self.child_id,

            "child_type": self.child_type.value,

        }





@dataclass

class Relationship:

    person1_id: str

    person2_id: str

    relation_type: str

    metadata: dict[str, Any] = field(default_factory=dict)





@dataclass

class FamilyGraph:

    persons: dict[str, Person] = field(default_factory=dict)

    marriages: dict[str, Marriage] = field(default_factory=dict)

    parent_child_links: list[ParentChildLink] = field(default_factory=list)

    relationships: list[Relationship] = field(default_factory=list)

    role_map: dict[str, str] = field(default_factory=dict)



    def add_person(self, person: Person, role: Optional[str] = None) -> Person:

        key = role.lower() if role else person.name.lower()

        if key in self.role_map and self.role_map[key] in self.persons:

            return self.persons[self.role_map[key]]

        self.persons[person.id] = person

        if role:

            self.role_map[role.lower()] = person.id

        self.role_map[person.name.lower()] = person.id

        return person



    def get_by_role_or_name(self, identifier: str) -> Optional[Person]:

        key = identifier.strip().lower()

        pid = self.role_map.get(key)

        if pid and pid in self.persons:

            return self.persons[pid]

        for p in self.persons.values():

            if p.name.lower() == key:

                return p

        return None



    def to_dict(self) -> dict[str, Any]:

        return {

            "persons": [p.to_dict() for p in self.persons.values()],

            "marriages": [m.to_dict() for m in self.marriages.values()],

            "parent_child_links": [l.to_dict() for l in self.parent_child_links],

            "relationships": [

                {

                    "person1_id": r.person1_id,

                    "person2_id": r.person2_id,

                    "relation_type": r.relation_type,

                    "metadata": r.metadata,

                }

                for r in self.relationships

            ],

            "role_map": self.role_map,

        }



    @classmethod

    def from_dict(cls, data: dict[str, Any]) -> "FamilyGraph":

        graph = cls()

        for p in data.get("persons", []):

            person = Person.from_dict(p)

            graph.persons[person.id] = person

        graph.role_map = data.get("role_map", {})

        for m in data.get("marriages", []):

            marriage = Marriage.from_dict(m)

            graph.marriages[marriage.id] = marriage

        for link in data.get("parent_child_links", []):

            graph.parent_child_links.append(

                ParentChildLink(

                    parent_ids=link["parent_ids"],

                    child_id=link["child_id"],

                    child_type=ChildType(link.get("child_type", "biological")),

                )

            )

        for r in data.get("relationships", []):

            graph.relationships.append(Relationship(**r))

        return graph

