#!/usr/bin/env python3
"""
Add skills, talents, traits, and powers as embedded items to NPC/enemy actors.

Reads ORIGINAL notes from git (commit 56db5cd, before format fix) to parse
SKILLS/TALENTS/TRAITS sections, then adds properly formatted DH2E items
to the CURRENT (already fixed) JSON files.

Also restores the full notes text into details.notes (which was truncated
by the double-run of fix-actor-data.py).
"""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRE_FIX_COMMIT = "56db5cd"

# ─── Skill → linked characteristic mapping ───────────────────────────────────
SKILL_CHARS = {
    "Acrobatics": "ag", "Athletics": "s", "Awareness": "per",
    "Charm": "fel", "Command": "fel", "Commerce": "int",
    "Common Lore": "int", "Deceive": "fel", "Dodge": "ag",
    "Forbidden Lore": "int", "Inquiry": "fel", "Interrogation": "wp",
    "Intimidate": "s", "Linguistics": "int", "Logic": "int",
    "Medicae": "int", "Navigate": "int", "Operate": "ag",
    "Parry": "ws", "Psyniscience": "per", "Scholastic Lore": "int",
    "Scrutiny": "per", "Security": "int", "Sleight of Hand": "ag",
    "Stealth": "ag", "Survival": "per", "Tech-Use": "int",
    "Trade": "int",
}

# ─── Trait → category mapping ─────────────────────────────────────────────────
TRAIT_CATEGORIES = {
    "Fear": "mental", "Dark Sight": "physical",
    "Unnatural Strength": "physical", "Unnatural Toughness": "physical",
    "Unnatural Willpower": "mental", "Unnatural Agility": "physical",
    "From Beyond": "warp", "Warp-Touched": "warp", "Warp Instability": "warp",
    "Regeneration": "physical", "Machine": "physical",
    "Size": "physical", "Flyer": "movement",
    "Bestial": "mental", "Quadruped": "movement",
    "Daemonic": "warp", "Fearless": "mental",
    "Mindless": "mental", "Shambling": "movement", "Undying": "warp",
    "Natural Armor": "physical", "Natural Armour": "physical",
    "Psyker": "warp", "Warp Seer": "warp",
    "Mechanicus Implants": "physical", "Multiple Arms": "physical",
    "Latent Psyker": "warp", "Barovus Native": "physical",
    "Disturbing": "mental", "Warp-Animated": "warp",
}

# ─── Power → discipline mapping ──────────────────────────────────────────────
POWER_DISCIPLINES = {
    "Warp Fire": "Pyromancy",
    "Telekinesis": "Telekinesis",
    "Telekinetic Control": "Telekinesis",
    "Telekinetic Storm": "Telekinesis",
    "Domination": "Telepathy",
    "Psychic Shriek": "Telepathy",
    "Flesh Warp": "Biomancy",
    "Warp Storm": "Warp",
    "Warp Lightning": "Warp",
    "Iron Arm": "Biomancy",
    "Psychic Scream": "Telepathy",
    "True Divination": "Divination",
}

# ─── ID counter ───────────────────────────────────────────────────────────────
_id_counter = 0
def next_id():
    global _id_counter
    _id_counter += 1
    return f"ski11ta1ent{_id_counter:04d}"


# ─── Parsing helpers ──────────────────────────────────────────────────────────

def split_respecting_parens(text):
    """Split on commas, but not inside parentheses."""
    result = []
    depth = 0
    current = []
    for char in text:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ',' and depth == 0:
            result.append(''.join(current).strip())
            current = []
            continue
        current.append(char)
    if current:
        result.append(''.join(current).strip())
    return [r for r in result if r]


def extract_section(notes, section_name):
    """Extract entries from 'SKILLS: ...' etc. in notes text."""
    pattern = rf'{section_name}:\s*(.+?)(?:\.\n|\n\n|\n[A-Z]{{2,}}[:\s]|$)'
    match = re.search(pattern, notes, re.DOTALL)
    if not match:
        return []
    text = match.group(1).strip()
    text = re.sub(r'\s+', ' ', text).rstrip('.')
    return split_respecting_parens(text)


def extract_special_abilities(notes):
    """Extract bullet-point special abilities."""
    abilities = {}
    pattern = r'(?:SPECIAL ABILITIES|SPECIAL RULES):\s*\n*(.*?)(?:\n(?:CASTLE|PHASE|DESTRUCTION|FOUR|GM |TACTICS:|GEAR:)|$)'
    match = re.search(pattern, notes, re.DOTALL)
    if not match:
        return abilities

    text = match.group(1).strip()
    parts = re.split(r'•\s*', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        dash_match = re.match(r'(.+?)\s*[—–]\s*(.+)', part, re.DOTALL)
        if dash_match:
            name = dash_match.group(1).strip()
            desc = dash_match.group(2).strip()
            abilities[name] = desc
    return abilities


def extract_psychic_powers(notes):
    """Extract psychic powers section."""
    powers = {}
    pattern = r'PSYCHIC POWERS:\s*\n*(.*?)(?:\n(?:SPECIAL|GM |TACTICS:)|$)'
    match = re.search(pattern, notes, re.DOTALL)
    if not match:
        return powers

    text = match.group(1).strip()
    parts = re.split(r'•\s*', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        dash_match = re.match(r'(.+?)\s*[—–]\s*(.+)', part, re.DOTALL)
        if dash_match:
            name = dash_match.group(1).strip()
            desc = dash_match.group(2).strip()
            powers[name] = desc
    return powers


# ─── Item builders ────────────────────────────────────────────────────────────

def make_skill(entry):
    """Parse 'Command +20' or 'Forbidden Lore (Warp, Daemonology) +20'."""
    entry = entry.strip().rstrip('.')

    adv_match = re.search(r'\+(\d+)$', entry)
    if adv_match:
        advancement = int(adv_match.group(1)) // 10
        name = entry[:adv_match.start()].strip()
    else:
        advancement = 0
        name = entry

    spec_match = re.match(r'^(.+?)\s*\((.+?)\)$', name)
    if spec_match:
        base_name = spec_match.group(1).strip()
        spec_text = spec_match.group(2).strip()

        # Multiple specializations: "Common Lore (Imperial, Ecclesiarchy)"
        if ',' in spec_text:
            items = []
            for spec in spec_text.split(','):
                spec = spec.strip()
                full_name = f"{base_name} ({spec})"
                linked = SKILL_CHARS.get(base_name, "int")
                items.append({
                    "_id": next_id(),
                    "name": full_name,
                    "type": "skill",
                    "img": "systems/dh2e/icons/items/skill.svg",
                    "system": {
                        "description": "",
                        "linkedCharacteristic": linked,
                        "advancement": advancement,
                        "isSpecialist": True,
                        "specialization": spec,
                    }
                })
            return items

        linked = SKILL_CHARS.get(base_name, "int")
        return [{
            "_id": next_id(),
            "name": name,
            "type": "skill",
            "img": "systems/dh2e/icons/items/skill.svg",
            "system": {
                "description": "",
                "linkedCharacteristic": linked,
                "advancement": advancement,
                "isSpecialist": True,
                "specialization": spec_text,
            }
        }]

    linked = SKILL_CHARS.get(name, "int")
    return [{
        "_id": next_id(),
        "name": name,
        "type": "skill",
        "img": "systems/dh2e/icons/items/skill.svg",
        "system": {
            "description": "",
            "linkedCharacteristic": linked,
            "advancement": advancement,
            "isSpecialist": False,
            "specialization": "",
        }
    }]


def make_talent(entry):
    """Parse 'Swift Attack' or 'Resistance (Psychic Powers)'."""
    name = entry.strip().rstrip('.')
    spec_match = re.match(r'^(.+?)\s*\((.+?)\)$', name)
    specialist = bool(spec_match)
    return {
        "_id": next_id(),
        "name": name,
        "type": "talent",
        "img": "systems/dh2e/icons/items/talent.svg",
        "system": {
            "description": "",
            "tier": 1,
            "aptitudes": [],
            "prerequisites": "",
            "specialist": specialist,
        }
    }


def make_trait(entry, description=""):
    """Parse 'Fear (4)' or 'Unnatural Strength (x2)'."""
    name = entry.strip().rstrip('.')
    has_rating = False
    rating = 0

    num_match = re.match(r'^(.+?)\s*\((\d+)\)$', name)
    if num_match:
        base = num_match.group(1).strip()
        rating = int(num_match.group(2))
        has_rating = True
        category = TRAIT_CATEGORIES.get(base, "")
    else:
        x_match = re.match(r'^(.+?)\s*\(x(\d+)\)$', name)
        if x_match:
            base = x_match.group(1).strip()
            rating = int(x_match.group(2))
            has_rating = True
            category = TRAIT_CATEGORIES.get(base, "")
        else:
            desc_match = re.match(r'^(.+?)\s*\((.+?)\)$', name)
            if desc_match:
                base = desc_match.group(1).strip()
                inner = desc_match.group(2).strip()
                category = TRAIT_CATEGORIES.get(base, "")
                inner_num = re.search(r'(\d+)', inner)
                if inner_num:
                    rating = int(inner_num.group(1))
                    has_rating = True
            else:
                category = TRAIT_CATEGORIES.get(name, "")

    return {
        "_id": next_id(),
        "name": name,
        "type": "trait",
        "img": "systems/dh2e/icons/default-icons/trait.svg",
        "system": {
            "description": description,
            "rules": [],
            "hasRating": has_rating,
            "rating": rating,
            "category": category,
        }
    }


def make_power(name, description="", discipline="", action="Half Action",
               range_str="", sustained=False, focus_mod=0):
    return {
        "_id": next_id(),
        "name": name,
        "type": "power",
        "img": "systems/dh2e/icons/items/power.svg",
        "system": {
            "description": description,
            "discipline": discipline,
            "cost": 200,
            "prerequisites": "",
            "focusTest": "wp",
            "focusModifier": focus_mod,
            "range": range_str,
            "sustained": sustained,
            "action": action,
            "subtype": "",
            "opposed": False,
        }
    }


# ─── Main processing ─────────────────────────────────────────────────────────

def load_original_data(rel_path):
    """Load the pre-fix version of a file from git."""
    full_path = f"{rel_path}"
    result = subprocess.run(
        ["git", "show", f"{PRE_FIX_COMMIT}:{full_path}"],
        capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        print(f"  Warning: could not load {full_path} from {PRE_FIX_COMMIT}")
        return None
    return json.loads(result.stdout)


def build_notes(original_actor):
    """Reconstruct the full details.notes from original actor fields."""
    sys = original_actor.get("system", {})
    desc = sys.get("description", "")
    notes = sys.get("notes", "")
    threat = sys.get("threatRating", "")
    movement = sys.get("movement", None)

    parts = []
    if desc:
        parts.append(desc)
    if threat:
        parts.append(f"\nTHREAT RATING: {threat}")
    if movement:
        mv = movement
        parts.append(
            f"\nMOVEMENT: Half {mv.get('half', 0)}, Full {mv.get('full', 0)}, "
            f"Charge {mv.get('charge', 0)}, Run {mv.get('run', 0)}"
        )
    if notes:
        parts.append(f"\n{notes}")

    return "\n".join(parts)


def process_actor(current_actor, original_actor):
    """Add items to current actor based on original actor's notes."""
    orig_notes = original_actor.get("system", {}).get("notes", "")
    name = current_actor.get("name", "")

    if not orig_notes:
        return 0

    # Restore full notes text (was truncated by double-run of fix script)
    full_notes = build_notes(original_actor)
    current_actor["system"]["details"]["notes"] = full_notes

    new_items = []

    # Parse SKILLS
    skill_entries = extract_section(orig_notes, "SKILLS")
    for entry in skill_entries:
        new_items.extend(make_skill(entry))

    # Parse TALENTS
    talent_entries = extract_section(orig_notes, "TALENTS")
    for entry in talent_entries:
        new_items.append(make_talent(entry))

    # Parse TRAITS
    trait_entries = extract_section(orig_notes, "TRAITS")
    for entry in trait_entries:
        new_items.append(make_trait(entry))

    # Parse SPECIAL ABILITIES/RULES as traits with descriptions
    special_abilities = extract_special_abilities(orig_notes)
    for sa_name, sa_desc in special_abilities.items():
        already = any(
            item["name"].split("(")[0].strip() == sa_name.split("(")[0].strip()
            for item in new_items if item["type"] == "trait"
        )
        if not already:
            new_items.append(make_trait(sa_name, description=sa_desc))

    # Parse PSYCHIC POWERS with discipline/action/range inference
    psychic_powers = extract_psychic_powers(orig_notes)
    for pw_name, pw_desc in psychic_powers.items():
        # Infer discipline from power name
        discipline = POWER_DISCIPLINES.get(pw_name, "")
        # Infer action from description
        action = "Full Action" if "Full Action" in pw_desc else "Half Action"
        # Infer sustained
        sustained = "Half Action" if "sustained" in pw_desc.lower() else False
        # Infer range from description
        range_str = ""
        range_match = re.search(r'(\d+m\s*(?:cone|radius)?)', pw_desc)
        if range_match:
            range_str = range_match.group(1)
        elif "touch" in pw_desc.lower():
            range_str = "Touch"
        new_items.append(make_power(pw_name, description=pw_desc,
                                    discipline=discipline, action=action,
                                    range_str=range_str, sustained=sustained))

    if new_items:
        if "items" not in current_actor:
            current_actor["items"] = []
        # Remove any existing skill/talent/trait/power items (idempotent re-run)
        item_types_to_add = {"skill", "talent", "trait", "power"}
        current_actor["items"] = [
            i for i in current_actor["items"]
            if i.get("type") not in item_types_to_add
        ]
        current_actor["items"].extend(new_items)

    n_skills = sum(1 for i in new_items if i["type"] == "skill")
    n_talents = sum(1 for i in new_items if i["type"] == "talent")
    n_traits = sum(1 for i in new_items if i["type"] == "trait")
    n_powers = sum(1 for i in new_items if i["type"] == "power")
    print(f"    {name}: +{len(new_items)} items "
          f"({n_skills}s {n_talents}ta {n_traits}tr {n_powers}p)")
    return len(new_items)


def process_file(rel_path):
    """Process a single actor file."""
    filepath = ROOT / rel_path
    print(f"Processing {filepath.name}...")

    # Load current (fixed-format) data
    with open(filepath, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    # Load original (pre-fix) data from git
    original_data = load_original_data(rel_path)
    if original_data is None:
        return

    # Build lookup by name
    orig_by_name = {a["name"]: a for a in original_data}

    total = 0
    for actor in current_data:
        name = actor.get("name", "")
        orig = orig_by_name.get(name)
        if orig:
            total += process_actor(actor, orig)
        else:
            print(f"    {name}: no original data found, skipping")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(current_data, f, indent=4, ensure_ascii=False)

    print(f"  Total: {total} new items added\n")


def main():
    process_file("data/actors/npcs.json")
    process_file("data/actors/enemies.json")
    print("Done. Rebuild packs with: node scripts/build-packs.mjs")


if __name__ == "__main__":
    main()
