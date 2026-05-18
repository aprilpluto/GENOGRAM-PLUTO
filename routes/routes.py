"""REST API routes — prefix URL tetap /api."""

from flask import Blueprint, jsonify, request

from core.parser import FamilyTextParser
from core.validator import FamilyValidator
from core.layout import GenogramLayoutEngine
from core.models import FamilyGraph

api_bp = Blueprint("api", __name__, url_prefix="/api")

parser = FamilyTextParser()
validator = FamilyValidator()
layout_engine = GenogramLayoutEngine()

TEMPLATES = {
    "nuclear": """Ayah: Budi, laki-laki, 55 tahun
Ibu: Sinta, perempuan, 50 tahun
Menikah tahun 1995
Anak 1: Andi, laki-laki, 25 tahun
Anak 2: Rina, perempuan, 20 tahun
Andi menikah dengan Maya, perempuan, 24 tahun""",
    "extended": """Kakek: Harto, laki-laki, 80 tahun, meninggal
Nenek: Wati, perempuan, 75 tahun
Ayah: Budi, laki-laki, 55 tahun
Ibu: Sinta, perempuan, 50 tahun
Menikah tahun 1995
Anak 1: Andi, laki-laki, 25 tahun
Anak 2: Rina, perempuan, 20 tahun""",
    "blended": """Ayah: Agus, laki-laki, 48 tahun
Ibu: Dewi, perempuan, 45 tahun
Anak 1: Fajar, laki-laki, 20 tahun, anak tiri
Anak 2: Lina, perempuan, 15 tahun
Menikah tahun 2010""",
}


@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "app": "Pluto Genogram Pintar",
        "platform": "vercel" if __import__("os").environ.get("VERCEL") else "local",
    })


@api_bp.route("/parse", methods=["POST"])
def parse_text():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not text.strip():
        return jsonify({"error": "Teks keluarga kosong."}), 400

    graph, parse_warnings, suggestions = parser.parse(text)
    validation = validator.validate(graph)
    layout = layout_engine.compute(graph)

    return jsonify({
        "success": True,
        "graph": validation["graph"],
        "layout": layout,
        "parse_warnings": parse_warnings,
        "suggestions": suggestions,
        "validation": {
            "valid": validation["valid"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "fixes": validation["fixes"],
        },
        "stats": {
            "persons": validation["person_count"],
            "marriages": validation["marriage_count"],
        },
    })


@api_bp.route("/validate", methods=["POST"])
def validate_graph():
    data = request.get_json(silent=True) or {}
    graph_data = data.get("graph")
    if not graph_data:
        return jsonify({"error": "Data graph diperlukan."}), 400
    graph = FamilyGraph.from_dict(graph_data)
    validation = validator.validate(graph)
    layout = layout_engine.compute(graph)
    return jsonify({**validation, "layout": layout})


@api_bp.route("/layout", methods=["POST"])
def compute_layout():
    data = request.get_json(silent=True) or {}
    graph_data = data.get("graph")
    if not graph_data:
        return jsonify({"error": "Data graph diperlukan."}), 400
    graph = FamilyGraph.from_dict(graph_data)
    layout = layout_engine.compute(graph)
    return jsonify({"layout": layout})


@api_bp.route("/templates", methods=["GET"])
def get_templates():
    return jsonify({
        "templates": [
            {"id": k, "name": k.replace("_", " ").title(), "text": v}
            for k, v in TEMPLATES.items()
        ]
    })


@api_bp.route("/templates/<template_id>", methods=["GET"])
def get_template(template_id: str):
    if template_id not in TEMPLATES:
        return jsonify({"error": "Template tidak ditemukan."}), 404
    return jsonify({"id": template_id, "text": TEMPLATES[template_id]})
