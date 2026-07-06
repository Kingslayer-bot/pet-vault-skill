def map_material_to_einvault_document(material):
    return {
        "title": material.get("source_file"),
        "category": material.get("type"),
        "companionName": material.get("pet_name"),
        "eventDate": material.get("date"),
        "localPath": material.get("raw_path"),
    }


def map_visit_to_einvault_health_event(visit):
    return {
        "type": "medical",
        "date": visit.get("date"),
        "summary": visit.get("reason") or "PetVault imported visit",
        "clinic": visit.get("clinic"),
    }
