#!/usr/bin/env python3
"""
One-shot script to fix NPC and enemy actor data to match the DH2E Foundry system format.

Fixes:
  1. Characteristics: {"value": X} → {"base": X, "advances": 0}
  2. Actor armour: {"value": X, "description": "..."} → per-location format
  3. Weapon items: restructure damage, rof, clip, qualities, class
  4. Armour items: "ap" → "locations", add equipped
  5. Add missing NPC template fields (fate, corruption, etc.)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DAMAGE_TYPE_MAP = {
    "E": "energy",
    "R": "rending",
    "I": "impact",
    "X": "explosive",
}

WEAPON_CLASS_MAP = {
    "Melee": "melee",
    "Pistol": "ranged",
    "Basic": "ranged",
    "Heavy": "ranged",
    "Thrown": "thrown",
}


def fix_characteristics(chars):
    """Convert {"value": X} to {"base": X, "advances": 0}."""
    fixed = {}
    for key, val in chars.items():
        if isinstance(val, dict):
            base = val.get("base", val.get("value", 25))
            advances = val.get("advances", 0)
            fixed[key] = {"base": base, "advances": advances}
        else:
            fixed[key] = {"base": val, "advances": 0}
    return fixed


def fix_actor_armour(actor):
    """Convert actor-level armour to per-location format, using embedded armour item if available."""
    # Try to get AP from embedded armour items
    armour_item = None
    for item in actor.get("items", []):
        if isinstance(item, dict) and item.get("type") == "armour":
            armour_item = item
            break

    if armour_item:
        sys_data = armour_item.get("system", {})
        # Check both "ap" (our format) and "locations" (correct format)
        locs = sys_data.get("ap", sys_data.get("locations", {}))
        return {
            "head": locs.get("head", 0),
            "rightArm": locs.get("rightArm", 0),
            "leftArm": locs.get("leftArm", 0),
            "body": locs.get("body", 0),
            "rightLeg": locs.get("rightLeg", 0),
            "leftLeg": locs.get("leftLeg", 0),
        }

    # Fallback: parse from old format
    old_armour = actor.get("system", {}).get("armour", {})
    if isinstance(old_armour, dict) and "value" in old_armour:
        val = old_armour["value"]
        # Assume uniform AP unless we can parse the description
        return {
            "head": val,
            "rightArm": val,
            "leftArm": val,
            "body": val,
            "rightLeg": val,
            "leftLeg": val,
        }

    # Already in correct format or missing
    return {"head": 0, "rightArm": 0, "leftArm": 0, "body": 0, "rightLeg": 0, "leftLeg": 0}


def parse_rof(rof_str):
    """Parse rate of fire string like 'S/2/-' into rof object."""
    if not rof_str or not isinstance(rof_str, str):
        return {"single": False, "semi": 0, "full": 0}

    parts = rof_str.split("/")
    if len(parts) != 3:
        return {"single": True, "semi": 0, "full": 0}

    single = parts[0].strip().upper() == "S"
    try:
        semi = int(parts[1].strip()) if parts[1].strip() != "-" else 0
    except ValueError:
        semi = 0
    try:
        full = int(parts[2].strip()) if parts[2].strip() != "-" else 0
    except ValueError:
        full = 0

    return {"single": single, "semi": semi, "full": full}


def fix_weapon(item_sys):
    """Convert weapon system data to DH2E format."""
    fixed = {}

    # Description
    fixed["description"] = item_sys.get("description", "")

    # Class: Melee/Pistol/Basic → melee/ranged
    raw_class = item_sys.get("class", "melee")
    fixed["class"] = WEAPON_CLASS_MAP.get(raw_class, raw_class.lower())

    # Range
    fixed["range"] = item_sys.get("range", 0)

    # Rate of fire
    if "rof" in item_sys:
        fixed["rof"] = item_sys["rof"]
    elif "rateOfFire" in item_sys:
        fixed["rof"] = parse_rof(item_sys["rateOfFire"])
    else:
        # Melee weapons don't have rof
        fixed["rof"] = {"single": False, "semi": 0, "full": 0}

    # Damage
    if isinstance(item_sys.get("damage"), dict):
        fixed["damage"] = item_sys["damage"]
    else:
        damage_str = item_sys.get("damage", "1d10")
        damage_type = item_sys.get("damageType", "I")
        fixed["damage"] = {
            "formula": damage_str,
            "type": DAMAGE_TYPE_MAP.get(damage_type, damage_type.lower()),
            "bonus": 0,
        }

    # Penetration
    fixed["penetration"] = item_sys.get("penetration", 0)

    # Clip/Magazine
    if isinstance(item_sys.get("clip"), dict):
        fixed["clip"] = item_sys["clip"]
    elif isinstance(item_sys.get("clip"), (int, float)):
        clip_val = int(item_sys["clip"])
        fixed["clip"] = {"value": clip_val, "max": clip_val}
    else:
        fixed["clip"] = {"value": 0, "max": 0}

    # Reload
    fixed["reload"] = item_sys.get("reload", "")

    # Weight
    fixed["weight"] = item_sys.get("weight", 0)

    # Qualities (convert from "special" string to array)
    if "qualities" in item_sys and isinstance(item_sys["qualities"], list):
        fixed["qualities"] = item_sys["qualities"]
    elif "special" in item_sys and item_sys["special"]:
        # Parse comma-separated special string
        fixed["qualities"] = [q.strip() for q in item_sys["special"].split(",") if q.strip()]
    else:
        fixed["qualities"] = []

    # Equipped
    fixed["equipped"] = item_sys.get("equipped", True)

    # Availability (keep if present)
    if "availability" in item_sys:
        fixed["availability"] = item_sys["availability"]

    return fixed


def fix_armour_item(item_sys):
    """Convert armour item system data to DH2E format."""
    fixed = {}

    fixed["description"] = item_sys.get("description", "")

    # Locations: convert from "ap" key to "locations" key
    locs = item_sys.get("ap", item_sys.get("locations", {}))
    fixed["locations"] = {
        "head": locs.get("head", 0),
        "rightArm": locs.get("rightArm", 0),
        "leftArm": locs.get("leftArm", 0),
        "body": locs.get("body", 0),
        "rightLeg": locs.get("rightLeg", 0),
        "leftLeg": locs.get("leftLeg", 0),
    }

    fixed["maxAgility"] = item_sys.get("maxAgility", 0)
    fixed["qualities"] = item_sys.get("qualities", [])
    fixed["weight"] = item_sys.get("weight", 0)
    fixed["equipped"] = item_sys.get("equipped", True)

    if "availability" in item_sys:
        fixed["availability"] = item_sys["availability"]

    return fixed


def fix_gear_item(item_sys):
    """Convert gear item system data to DH2E format."""
    fixed = {}
    fixed["description"] = item_sys.get("description", "")
    fixed["weight"] = item_sys.get("weight", 0)
    fixed["quantity"] = item_sys.get("quantity", 1)

    if "availability" in item_sys:
        fixed["availability"] = item_sys["availability"]

    return fixed


def fix_actor(actor):
    """Fix a single actor entry to match DH2E system format."""
    sys = actor.get("system", {})

    # 1. Fix characteristics
    if "characteristics" in sys:
        sys["characteristics"] = fix_characteristics(sys["characteristics"])

    # 2. Fix actor-level armour
    sys["armour"] = fix_actor_armour(actor)

    # 3. Add missing NPC template fields
    if "fate" not in sys:
        sys["fate"] = {"value": 0, "max": 0}
    if "fatigue" not in sys:
        sys["fatigue"] = 0
    if "corruption" not in sys:
        sys["corruption"] = 0
    if "insanity" not in sys:
        sys["insanity"] = 0
    if "influence" not in sys:
        sys["influence"] = 0
    if "xp" not in sys:
        sys["xp"] = {"total": 0, "spent": 0}
    if "aptitudes" not in sys:
        sys["aptitudes"] = []
    if "defeated" not in sys:
        sys["defeated"] = False

    # 4. Fix details structure - move notes and description
    old_notes = sys.pop("notes", "")
    old_desc = sys.get("description", "")
    old_threat = sys.pop("threatRating", "")
    old_movement = sys.pop("movement", None)

    # Build notes with all the rich text data
    notes_parts = []
    if old_desc:
        notes_parts.append(old_desc)
    if old_threat:
        notes_parts.append(f"\nTHREAT RATING: {old_threat}")
    if old_movement:
        mv = old_movement
        notes_parts.append(
            f"\nMOVEMENT: Half {mv.get('half', 0)}, Full {mv.get('full', 0)}, "
            f"Charge {mv.get('charge', 0)}, Run {mv.get('run', 0)}"
        )
    if old_notes:
        notes_parts.append(f"\n{old_notes}")

    combined_notes = "\n".join(notes_parts)

    # Keep description at top level for the system's description field
    # Put everything in details.notes
    sys["details"] = {
        "homeworld": "",
        "background": "",
        "role": old_threat if old_threat else "",
        "divination": "",
        "notes": combined_notes,
    }

    # 5. Fix items
    if "items" in actor and isinstance(actor["items"], list):
        for item in actor["items"]:
            if not isinstance(item, dict):
                continue
            item_sys = item.get("system", {})
            item_type = item.get("type", "")

            if item_type == "weapon":
                item["system"] = fix_weapon(item_sys)
            elif item_type == "armour":
                item["system"] = fix_armour_item(item_sys)
            elif item_type == "gear":
                item["system"] = fix_gear_item(item_sys)

    actor["system"] = sys
    return actor


def process_file(filepath):
    """Process a single JSON file."""
    print(f"Processing {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"  Skipping {filepath}: not an array")
        return

    for actor in data:
        fix_actor(actor)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"  Fixed {len(data)} actors")


def fix_ammunition_item(item_sys):
    """Convert ammunition item system data to DH2E format."""
    fixed = {}
    fixed["description"] = item_sys.get("description", "")
    fixed["damageModifier"] = item_sys.get("damageModifier", 0)
    fixed["damageType"] = item_sys.get("damageType", "")
    fixed["penetrationModifier"] = item_sys.get("penetrationModifier", 0)
    fixed["qualities"] = item_sys.get("qualities", [])
    fixed["quantity"] = item_sys.get("quantity", 1)
    fixed["weight"] = item_sys.get("weight", 0)
    # weaponType → weaponGroup
    fixed["weaponGroup"] = item_sys.get("weaponGroup", item_sys.get("weaponType", ""))
    if "availability" in item_sys:
        fixed["availability"] = item_sys["availability"]
    return fixed


def process_items_file(filepath):
    """Process a standalone items JSON file."""
    print(f"Processing {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"  Skipping: not an array")
        return

    for item in data:
        if not isinstance(item, dict):
            continue
        item_sys = item.get("system", {})
        item_type = item.get("type", "")

        if item_type == "weapon":
            item["system"] = fix_weapon(item_sys)
        elif item_type == "armour":
            item["system"] = fix_armour_item(item_sys)
        elif item_type == "gear":
            item["system"] = fix_gear_item(item_sys)
        elif item_type == "ammunition":
            item["system"] = fix_ammunition_item(item_sys)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"  Fixed {len(data)} items")


def main():
    # Fix actor files
    actor_files = [
        ROOT / "data" / "actors" / "npcs.json",
        ROOT / "data" / "actors" / "enemies.json",
    ]

    for filepath in actor_files:
        if filepath.exists():
            process_file(filepath)
        else:
            print(f"  Skipping {filepath}: not found")

    # Fix standalone item files
    item_files = [
        ROOT / "data" / "items" / "weapons.json",
        ROOT / "data" / "items" / "armour.json",
        ROOT / "data" / "items" / "gear.json",
        ROOT / "data" / "items" / "ammunition.json",
    ]

    for filepath in item_files:
        if filepath.exists():
            process_items_file(filepath)
        else:
            print(f"  Skipping {filepath}: not found")

    print("\nDone. Rebuild packs with: node scripts/build-packs.mjs")


if __name__ == "__main__":
    main()
