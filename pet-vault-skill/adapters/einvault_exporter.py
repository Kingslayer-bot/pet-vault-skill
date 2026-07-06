import json
from pathlib import Path

from einvault_mapper import map_material_to_einvault_document


def export_materials(materials_index_path, output_path):
    data = json.loads(Path(materials_index_path).read_text(encoding="utf-8"))
    exported = [map_material_to_einvault_document(item) for item in data.get("materials", [])]
    Path(output_path).write_text(json.dumps(exported, ensure_ascii=False, indent=2), encoding="utf-8")
    return exported
