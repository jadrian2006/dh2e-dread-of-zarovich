#!/usr/bin/env python3
"""
Idempotent refactoring script to bring all campaign data into full conformance
with the DH2E system's template.json schemas.

Changes:
  - Weapons: rename clip->magazine, add missing fields, fix melee rof
  - Armour/Gear: add craftsmanship
  - Ammunition: add craftsmanship, capacity, loadedRounds, forWeapon
  - Traits (embedded): add immunities, populate rules arrays
  - Traits (standalone): merge notes into description, add template fields
  - Objectives: rename issuer->assignedBy, merge notes, add fields
  - Actors: add eliteAdvances

All transformations use setdefault() or existence checks — safe to re-run.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ─── Trait → Rule Element + Immunities mapping ─────────────────────────────────

def slugify(name):
    """Convert a trait name to a slug for RollOption keys."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def parse_trait_name(name):
    """Parse 'Fear (4)' or 'Unnatural Strength (x2)' or 'Size (Hulking)'."""
    # Numeric rating: Fear (4)
    m = re.match(r'^(.+?)\s*\((\d+)\)$', name)
    if m:
        return m.group(1).strip(), int(m.group(2))

    # Multiplier rating: Unnatural Strength (x2)
    m = re.match(r'^(.+?)\s*\(x(\d+)\)$', name)
    if m:
        return m.group(1).strip(), int(m.group(2))

    # Descriptive parens: Size (Hulking)
    m = re.match(r'^(.+?)\s*\((.+?)\)$', name)
    if m:
        base = m.group(1).strip()
        inner = m.group(2).strip()
        num = re.search(r'(\d+)', inner)
        return base, int(num.group(1)) if num else 0

    return name.strip(), 0


def get_trait_rules_and_immunities(name, rating):
    """Return (rules_list, immunities_list) for a given trait base name + rating."""
    base, _ = parse_trait_name(name)
    # Use the parsed rating from the actual trait name
    _, parsed_rating = parse_trait_name(name)
    if parsed_rating:
        rating = parsed_rating

    rules = []
    immunities = []

    if base == "Fear":
        rules.append({"key": "RollOption", "option": "self:fear"})

    elif base == "Dark Sight":
        rules.append({"key": "RollOption", "option": "self:dark-sight"})

    elif base == "Unnatural Strength":
        rules.append({"key": "FlatModifier", "domain": "damage", "value": "rating"})

    elif base == "Unnatural Toughness":
        rules.append({"key": "AdjustToughness", "mode": "add", "value": "rating"})

    elif base == "Unnatural Willpower":
        rules.append({"key": "FlatModifier", "domain": "characteristic:wp", "value": "rating"})

    elif base == "Unnatural Agility":
        rules.append({"key": "FlatModifier", "domain": "characteristic:ag", "value": "rating"})

    elif base == "From Beyond":
        rules.append({"key": "RollOption", "option": "self:from-beyond"})
        immunities = ["Fear", "Pinning", "Insanity"]

    elif base == "Regeneration":
        rules.append({"key": "RollOption", "option": "self:regeneration"})

    elif base in ("Natural Armor", "Natural Armour"):
        rules.append({"key": "FlatModifier", "domain": "armour", "value": "rating"})

    elif base == "Daemonic":
        rules.append({"key": "AdjustToughness", "mode": "add", "value": "rating"})
        rules.append({"key": "RollOption", "option": "self:daemonic"})
        immunities = ["Fear", "Pinning", "Disease", "Poison"]

    elif base == "Machine":
        rules.append({"key": "FlatModifier", "domain": "armour", "value": "rating"})
        rules.append({"key": "RollOption", "option": "self:machine"})
        immunities = ["Fear", "Pinning", "Disease", "Poison"]

    elif base == "Mindless":
        rules.append({"key": "RollOption", "option": "self:mindless"})
        immunities = ["Fear", "Pinning", "psychic-mind"]

    elif base == "Fearless":
        rules.append({"key": "RollOption", "option": "self:fearless"})
        immunities = ["Fear"]

    elif base == "Stuff of Nightmares":
        rules.append({"key": "RollOption", "option": "self:stuff-of-nightmares"})
        immunities = ["critical", "bleeding", "stun"]

    elif base == "Incorporeal":
        rules.append({"key": "Resistance", "damageType": "impact", "mode": "half"})
        rules.append({"key": "Resistance", "damageType": "rending", "mode": "half"})
        rules.append({"key": "Resistance", "damageType": "explosive", "mode": "half"})
        rules.append({"key": "RollOption", "option": "self:incorporeal"})

    elif base == "Brutal Charge":
        rules.append({
            "key": "FlatModifier", "domain": "damage",
            "value": "rating", "predicate": ["action:charge"],
        })

    elif base == "Size":
        # Extract size category from full name
        m = re.match(r'^Size\s*\((.+?)\)$', name)
        cat = slugify(m.group(1)) if m else "average"
        rules.append({"key": "RollOption", "option": f"self:size:{cat}"})

    elif base in ("Flyer", "Toxic", "Shambling", "Quadruped", "Bestial",
                   "Undying", "Warp Instability", "Warp-Touched",
                   "Multiple Arms", "Mechanicus Implants", "Psyker",
                   "Warp Seer", "Disturbing", "Warp-Animated"):
        rules.append({"key": "RollOption", "option": f"self:{slugify(base)}"})

    else:
        # Unknown/campaign-custom: generic RollOption
        rules.append({"key": "RollOption", "option": f"self:{slugify(base)}"})

    return rules, immunities


# ─── Item refactoring functions ─────────────────────────────────────────────────

def refactor_weapon(sys):
    """Refactor a weapon's system data in place."""
    # Rename clip -> magazine
    if "clip" in sys and "magazine" not in sys:
        sys["magazine"] = sys.pop("clip")
    sys.setdefault("magazine", {"value": 0, "max": 0})

    # Add missing fields
    sys.setdefault("craftsmanship", "common")
    sys.setdefault("weaponGroup", "")
    sys.setdefault("loadedAmmoId", "")
    sys.setdefault("loadedMagazineName", "")
    sys.setdefault("loadedRounds", [])
    sys.setdefault("reloadProgress", 0)
    sys.setdefault("rules", [])

    # Infer loadType
    if "loadType" not in sys:
        mag = sys.get("magazine", {})
        is_ranged = sys.get("class") in ("ranged", "thrown")
        max_val = mag.get("max", 0) if isinstance(mag, dict) else 0
        sys["loadType"] = "magazine" if is_ranged and max_val > 0 else ""

    # Fix melee weapons: rof.single should be true (template default)
    if sys.get("class") == "melee":
        rof = sys.get("rof", {})
        if isinstance(rof, dict) and not rof.get("single"):
            rof["single"] = True


def refactor_armour(sys):
    """Refactor an armour item's system data in place."""
    sys.setdefault("craftsmanship", "common")


def refactor_gear(sys):
    """Refactor a gear item's system data in place."""
    sys.setdefault("craftsmanship", "common")


def refactor_ammunition(sys):
    """Refactor an ammunition item's system data in place."""
    sys.setdefault("craftsmanship", "common")
    # capacity mirrors quantity
    if "capacity" not in sys:
        sys["capacity"] = sys.get("quantity", 1)
    sys.setdefault("loadedRounds", [])
    sys.setdefault("forWeapon", "")


def refactor_trait(sys, name):
    """Refactor an embedded trait's system data in place."""
    rating = sys.get("rating", 0)
    rules, immunities = get_trait_rules_and_immunities(name, rating)

    # Always set immunities from mapping
    sys.setdefault("immunities", [])
    if immunities:
        sys["immunities"] = immunities

    # Always regenerate rules from mapping (overwrite old wrong-format rules)
    if rules:
        sys["rules"] = rules


def refactor_standalone_trait(item):
    """Refactor a standalone campaign trait item."""
    sys = item.get("system", {})

    # Merge notes into description (template has no notes field)
    notes = sys.pop("notes", "")
    if notes:
        desc = sys.get("description", "")
        if notes not in desc:
            sys["description"] = f"{desc}\n{notes}" if desc else notes

    # Add missing template fields
    sys.setdefault("rules", [])
    sys.setdefault("hasRating", False)
    sys.setdefault("rating", 0)
    sys.setdefault("category", "")
    sys.setdefault("immunities", [])

    # Always regenerate campaign-specific rules (overwrite old wrong-format rules)
    name = item.get("name", "")
    if True:
        slug = slugify(name)
        if name == "Latent Psyker":
            sys["rules"] = [
                {"key": "FlatModifier", "domain": "initiative", "value": 10},
                {"key": "RollOption", "option": "self:latent-psyker"},
            ]
        else:
            sys["rules"] = [{"key": "RollOption", "option": f"self:{slug}"}]


def refactor_objective(sys):
    """Refactor an objective's system data in place."""
    # Rename issuer -> assignedBy
    if "issuer" in sys and "assignedBy" not in sys:
        sys["assignedBy"] = sys.pop("issuer")
    sys.setdefault("assignedBy", "")

    # Merge notes into description
    notes = sys.pop("notes", "")
    if notes:
        desc = sys.get("description", "")
        if notes not in desc:
            sys["description"] = f"{desc}\n{notes}" if desc else notes

    # Add missing template fields
    sys.setdefault("timestamp", 0)
    sys.setdefault("completedTimestamp", 0)
    sys.setdefault("scope", "warband")


def refactor_embedded_item(item):
    """Refactor a single embedded item on an actor."""
    if not isinstance(item, dict):
        return
    item_type = item.get("type", "")
    sys = item.get("system", {})

    if item_type == "weapon":
        refactor_weapon(sys)
    elif item_type == "armour":
        refactor_armour(sys)
    elif item_type == "gear":
        refactor_gear(sys)
    elif item_type == "ammunition":
        refactor_ammunition(sys)
    elif item_type == "trait":
        refactor_trait(sys, item.get("name", ""))


def refactor_actor(actor):
    """Refactor a single actor entry."""
    sys = actor.get("system", {})

    # Add eliteAdvances
    sys.setdefault("eliteAdvances", [])

    # Process embedded items
    for item in actor.get("items", []):
        refactor_embedded_item(item)


# ─── File processors ────────────────────────────────────────────────────────────

def process_items_file(filepath, item_type):
    """Process a standalone items JSON file."""
    if not filepath.exists():
        print(f"  Skipping {filepath}: not found")
        return

    print(f"Processing {filepath.name}...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"  Skipping: not an array")
        return

    for item in data:
        if not isinstance(item, dict):
            continue
        sys = item.get("system", {})

        if item_type == "weapon":
            refactor_weapon(sys)
        elif item_type == "armour":
            refactor_armour(sys)
        elif item_type == "gear":
            refactor_gear(sys)
        elif item_type == "ammunition":
            refactor_ammunition(sys)
        elif item_type == "trait":
            refactor_standalone_trait(item)
        elif item_type == "objective":
            refactor_objective(sys)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"  Refactored {len(data)} {item_type}(s)")


def process_actors_file(filepath):
    """Process an actors JSON file."""
    if not filepath.exists():
        print(f"  Skipping {filepath}: not found")
        return

    print(f"Processing {filepath.name}...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"  Skipping: not an array")
        return

    for actor in data:
        refactor_actor(actor)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"  Refactored {len(data)} actors")


def bump_version():
    """Bump module.json version to 0.4.7."""
    filepath = ROOT / "module.json"
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    old_version = data.get("version", "")
    new_version = "0.4.7"

    if old_version == new_version:
        print(f"module.json already at v{new_version}")
        return

    data["version"] = new_version
    # Update manifest and download URLs
    if "manifest" in data:
        data["manifest"] = data["manifest"].replace(
            f"v{old_version}", f"v{new_version}"
        ).replace(old_version, new_version)
    if "download" in data:
        data["download"] = data["download"].replace(
            f"v{old_version}", f"v{new_version}"
        ).replace(old_version, new_version)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"module.json: {old_version} -> {new_version}")


def main():
    print("=== Refactoring campaign data to match DH2E system schemas ===\n")

    # Standalone items
    items_dir = ROOT / "data" / "items"
    process_items_file(items_dir / "weapons.json", "weapon")
    process_items_file(items_dir / "armour.json", "armour")
    process_items_file(items_dir / "gear.json", "gear")
    process_items_file(items_dir / "ammunition.json", "ammunition")
    process_items_file(items_dir / "traits.json", "trait")
    process_items_file(items_dir / "objectives.json", "objective")

    print()

    # Actor files (embedded items + actor-level fields)
    actors_dir = ROOT / "data" / "actors"
    process_actors_file(actors_dir / "npcs.json")
    process_actors_file(actors_dir / "enemies.json")

    print()

    # Version bump
    bump_version()

    print("\nDone. Rebuild packs with: node scripts/build-packs.mjs")


if __name__ == "__main__":
    main()
