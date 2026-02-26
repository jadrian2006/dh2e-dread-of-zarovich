/**
 * Build script: compiles JSON data files into Foundry VTT LevelDB compendium packs.
 *
 * Adapted from dh2e-data and community-pack-template for the
 * Dread of Zarovich campaign module.
 *
 * Usage: node scripts/build-packs.mjs
 *
 * Prerequisites: npm install classic-level
 */

import { ClassicLevel } from "classic-level";
import { readFileSync, rmSync, existsSync, mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

/** Generate a Foundry-compatible 16-char random ID */
function foundryId() {
    return randomUUID().replace(/-/g, "").slice(0, 16);
}

/** Current timestamp for _stats */
function now() {
    return Date.now();
}

/**
 * Pack definitions — maps each compendium to its source data file(s) and type.
 *
 * collection values: "actors", "items", "journal", "scenes", "tables"
 */
const PACKS = [
    // Actors
    { name: "npcs", file: "data/actors/npcs.json", collection: "actors" },
    { name: "enemies", file: "data/actors/enemies.json", collection: "actors" },

    // Items
    { name: "weapons", file: "data/items/weapons.json", collection: "items" },
    { name: "armour", file: "data/items/armour.json", collection: "items" },
    { name: "gear", file: "data/items/gear.json", collection: "items" },
    { name: "ammunition", file: "data/items/ammunition.json", collection: "items" },
    { name: "objectives", file: "data/items/objectives.json", collection: "items" },
    { name: "traits", file: "data/items/traits.json", collection: "items" },

    // Journals
    { name: "handouts", file: "data/journals/handouts.json", collection: "journal" },
    { name: "locations", file: "data/journals/locations.json", collection: "journal" },
    { name: "npc-profiles", file: "data/journals/npcs.json", collection: "journal" },
    { name: "campaign-rules", file: "data/journals/rules.json", collection: "journal" },

    // Scenes
    { name: "scenes", file: "data/scenes/scenes.json", collection: "scenes" },

    // Tables
    { name: "tables", file: "data/tables/tables.json", collection: "tables" },
];

/**
 * Build a single compendium pack from its JSON source.
 */
async function buildPack(packDef) {
    const dataPath = resolve(ROOT, packDef.file);
    if (!existsSync(dataPath)) {
        console.warn(`  ⚠ Skipping ${packDef.name}: ${packDef.file} not found`);
        return 0;
    }

    const packDir = resolve(ROOT, "packs", packDef.name);

    // Clear existing pack
    if (existsSync(packDir)) {
        rmSync(packDir, { recursive: true });
    }
    mkdirSync(packDir, { recursive: true });

    const raw = readFileSync(dataPath, "utf-8");
    const entries = JSON.parse(raw);

    const db = new ClassicLevel(packDir, {
        keyEncoding: "utf8",
        valueEncoding: "json",
    });
    await db.open();

    let count = 0;
    const batch = db.batch();

    for (const entry of entries) {
        if (!entry._id) entry._id = foundryId();

        // Add Foundry v13 metadata
        if (!entry._stats) {
            entry._stats = {
                coreVersion: "13.351",
                systemId: "dh2e",
                systemVersion: "0.1.0",
                createdTime: now(),
                modifiedTime: now(),
                lastModifiedBy: "dh2eDreadZarvch0",
            };
        }

        // Foundry v13 LevelDB format: embedded documents (items, pages, results)
        // are stored as SEPARATE sublevel keys. The parent document's array
        // contains ONLY ID strings, not full objects.

        // Embedded items for actors → sublevel keys + ID-only array
        if (packDef.collection === "actors" && Array.isArray(entry.items)) {
            const itemIds = [];
            for (const item of entry.items) {
                if (typeof item === "object") {
                    if (!item._id) item._id = foundryId();
                    if (!item._stats) item._stats = { ...entry._stats };
                    batch.put(`!actors.items!${entry._id}.${item._id}`, item);
                    itemIds.push(item._id);
                }
            }
            entry.items = itemIds;
        }

        // Embedded pages for journal entries → sublevel keys + ID-only array
        if (packDef.collection === "journal" && Array.isArray(entry.pages)) {
            const pageIds = [];
            for (const page of entry.pages) {
                if (!page._id) page._id = foundryId();
                if (!page._stats) page._stats = { ...entry._stats };
                batch.put(`!journal.pages!${entry._id}.${page._id}`, page);
                pageIds.push(page._id);
            }
            entry.pages = pageIds;
        }

        // Embedded results for roll tables → sublevel keys + ID-only array
        if (packDef.collection === "tables" && Array.isArray(entry.results)) {
            const resultIds = [];
            for (const result of entry.results) {
                if (!result._id) result._id = foundryId();
                if (!result._stats) result._stats = { ...entry._stats };
                batch.put(`!tables.results!${entry._id}.${result._id}`, result);
                resultIds.push(result._id);
            }
            entry.results = resultIds;
        }

        // Store parent document (embedded arrays now contain only ID strings)
        const key = `!${packDef.collection}!${entry._id}`;
        batch.put(key, entry);
        count++;
    }

    await batch.write();
    await db.close();

    console.log(`  ✓ ${packDef.name}: ${count} entries`);
    return count;
}

/**
 * Also support building from individual scene files (vessel-of-lament-upper.json, etc.)
 * merged into a single scenes pack.
 */
async function buildScenesPack() {
    const scenesDir = resolve(ROOT, "data/scenes");
    const packDir = resolve(ROOT, "packs/scenes");

    if (!existsSync(scenesDir)) {
        console.warn("  ⚠ Skipping scenes: data/scenes/ not found");
        return 0;
    }

    // Check for individual scene files
    const { readdirSync } = await import("node:fs");
    const files = readdirSync(scenesDir).filter(
        (f) => f.endsWith(".json") && f !== "scenes.json"
    );

    if (files.length === 0) return 0; // Let the main PACKS handler deal with scenes.json

    // Clear existing pack
    if (existsSync(packDir)) {
        rmSync(packDir, { recursive: true });
    }
    mkdirSync(packDir, { recursive: true });

    const db = new ClassicLevel(packDir, {
        keyEncoding: "utf8",
        valueEncoding: "json",
    });
    await db.open();

    let count = 0;
    const batch = db.batch();

    for (const file of files) {
        const raw = readFileSync(resolve(scenesDir, file), "utf-8");
        const scenes = JSON.parse(raw);
        const list = Array.isArray(scenes) ? scenes : [scenes];

        for (const scene of list) {
            if (!scene._id) scene._id = foundryId();
            if (!scene._stats) {
                scene._stats = {
                    coreVersion: "13.351",
                    systemId: "dh2e",
                    systemVersion: "0.1.0",
                    createdTime: now(),
                    modifiedTime: now(),
                    lastModifiedBy: "dh2eDreadZarvch0",
                };
            }
            batch.put(`!scenes!${scene._id}`, scene);
            count++;
        }
    }

    await batch.write();
    await db.close();

    if (count > 0) {
        console.log(`  ✓ scenes (individual files): ${count} entries`);
    }
    return count;
}

async function main() {
    console.log("Building Dread of Zarovich compendium packs...\n");

    let total = 0;

    // Build individual scene files first (if they exist)
    const scenesFromFiles = await buildScenesPack();
    total += scenesFromFiles;

    for (const packDef of PACKS) {
        // Skip the combined scenes.json if we already built from individual files
        if (packDef.name === "scenes" && scenesFromFiles > 0) continue;
        total += await buildPack(packDef);
    }

    console.log(`\nDone. ${total} total entries built.`);
}

main().catch(console.error);
