/**
 * Dread of Zarovich — One-click import for all compendium content.
 *
 * On first activation, presents the GM with a dialog to import all
 * 114 entries across 14 packs into the world, organized into folders.
 * If content was already imported without folders, offers to organize it.
 */

const MODULE_ID = "dh2e-dread-of-zarovich";
const PARENT_NAME = "Dread of Zarovich";
const PARENT_COLOR = "#8b1a1a";

/**
 * Maps each compendium pack name to its document type and sub-folder name.
 * Sub-folders nest under a "Dread of Zarovich" parent folder for that type.
 * If `sub` is null, documents go directly in the parent folder.
 */
const PACK_FOLDERS = {
    "npcs":           { type: "Actor",        sub: "Major NPCs" },
    "enemies":        { type: "Actor",        sub: "Enemies & Creatures" },
    "weapons":        { type: "Item",         sub: "Weapons" },
    "armour":         { type: "Item",         sub: "Armour" },
    "gear":           { type: "Item",         sub: "Gear & Relics" },
    "ammunition":     { type: "Item",         sub: "Ammunition" },
    "objectives":     { type: "Item",         sub: "Mission Objectives" },
    "traits":         { type: "Item",         sub: "Campaign Traits" },
    "handouts":       { type: "JournalEntry", sub: "Player Handouts" },
    "locations":      { type: "JournalEntry", sub: "Locations" },
    "npc-profiles":   { type: "JournalEntry", sub: "NPC Profiles" },
    "campaign-rules": { type: "JournalEntry", sub: "Campaign Rules" },
    "scenes":         { type: "Scene",        sub: null },
    "tables":         { type: "RollTable",    sub: null },
};

/* ------------------------------------------------------------------ */
/*  Settings                                                          */
/* ------------------------------------------------------------------ */

Hooks.once("init", () => {
    game.settings.register(MODULE_ID, "imported", {
        name: "Content Imported",
        hint: "Whether the module content has been imported into this world.",
        scope: "world",
        config: false,
        type: Boolean,
        default: false,
    });
    game.settings.register(MODULE_ID, "organized", {
        name: "Content Organized",
        hint: "Whether imported content has been sorted into folders.",
        scope: "world",
        config: false,
        type: Boolean,
        default: false,
    });

    // Visible button in Module Settings to re-import content
    game.settings.registerMenu(MODULE_ID, "reimportMenu", {
        name: "Re-import & Overwrite Content",
        label: "Re-import All",
        hint: "Delete all previously imported Dread of Zarovich content and re-import fresh from the compendium packs. Use this after a module update to get the latest data.",
        icon: "fas fa-sync-alt",
        type: ReimportFormApplication,
        restricted: true, // GM only
    });
});

/* ------------------------------------------------------------------ */
/*  Ready hook — decide which dialog to show                          */
/* ------------------------------------------------------------------ */

Hooks.once("ready", async () => {
    if (!game.user.isGM) return;

    const imported = game.settings.get(MODULE_ID, "imported");
    const organized = game.settings.get(MODULE_ID, "organized");

    if (!imported) {
        showImportDialog();
    } else if (!organized) {
        showOrganizeDialog();
    }
});

/* ------------------------------------------------------------------ */
/*  Dialogs                                                           */
/* ------------------------------------------------------------------ */

function showImportDialog() {
    new Dialog({
        title: "Dread of Zarovich — Import Campaign Content",
        content: `
            <div style="margin-bottom: 12px;">
                <p>Import all <strong>Dread of Zarovich</strong> campaign content into this world?</p>
                <p>This will create <strong>114 entries</strong> across 14 compendium packs,
                organized into labelled folders:</p>
                <ul style="columns: 2; margin-top: 4px; font-size: 12px;">
                    <li>7 Major NPCs</li>
                    <li>10 Enemy stat blocks</li>
                    <li>8 Weapons</li>
                    <li>4 Armour sets</li>
                    <li>13 Gear &amp; Relics</li>
                    <li>4 Ammunition types</li>
                    <li>6 Mission Objectives</li>
                    <li>5 Campaign Traits</li>
                    <li>7 Player Handouts</li>
                    <li>12 Location entries</li>
                    <li>9 NPC Profiles</li>
                    <li>2 Campaign Rules</li>
                    <li>19 Scene templates</li>
                    <li>8 Roll Tables</li>
                </ul>
            </div>`,
        buttons: {
            import: {
                icon: '<i class="fas fa-download"></i>',
                label: "Import All",
                callback: () => importAllContent(),
            },
            later: {
                icon: '<i class="fas fa-clock"></i>',
                label: "Remind Me Later",
            },
            never: {
                icon: '<i class="fas fa-times"></i>',
                label: "Don\u2019t Ask Again",
                callback: () => {
                    game.settings.set(MODULE_ID, "imported", true);
                    game.settings.set(MODULE_ID, "organized", true);
                },
            },
        },
        default: "import",
    }).render(true);
}

function showOrganizeDialog() {
    new Dialog({
        title: "Dread of Zarovich — Organize Content",
        content: `
            <div style="margin-bottom: 12px;">
                <p>Your <strong>Dread of Zarovich</strong> content was imported without
                folder organization.</p>
                <p>This will create a <strong>\u201CDread of Zarovich\u201D</strong> folder tree
                in each sidebar tab and move all 114 imported documents into the
                appropriate sub-folders. No documents will be deleted or modified
                \u2014 only sorted.</p>
            </div>`,
        buttons: {
            organize: {
                icon: '<i class="fas fa-folder-tree"></i>',
                label: "Organize Now",
                callback: () => organizeExistingContent(),
            },
            later: {
                icon: '<i class="fas fa-clock"></i>',
                label: "Remind Me Later",
            },
            never: {
                icon: '<i class="fas fa-times"></i>',
                label: "Don\u2019t Ask Again",
                callback: () => {
                    game.settings.set(MODULE_ID, "organized", true);
                },
            },
        },
        default: "organize",
    }).render(true);
}

/* ------------------------------------------------------------------ */
/*  Folder creation — idempotent find-or-create                       */
/* ------------------------------------------------------------------ */

/**
 * Build the full folder tree and return a Map<packName, folderId>.
 * Safe to call multiple times — reuses existing folders by name/type/parent.
 */
async function createFolderStructure() {
    const folderMap = new Map();

    // Collect unique document types that need a parent folder
    const typeSet = new Set(Object.values(PACK_FOLDERS).map((v) => v.type));

    // Create (or find) parent folders — one per document type
    const parentFolders = new Map();
    for (const docType of typeSet) {
        let parent = game.folders.find(
            (f) => f.name === PARENT_NAME && f.type === docType && !f.folder
        );
        if (!parent) {
            parent = await Folder.create({
                name: PARENT_NAME,
                type: docType,
                color: PARENT_COLOR,
                folder: null,
            });
        }
        parentFolders.set(docType, parent);
    }

    // Create (or find) sub-folders, and populate the map
    for (const [packName, cfg] of Object.entries(PACK_FOLDERS)) {
        const parent = parentFolders.get(cfg.type);

        if (!cfg.sub) {
            // No sub-folder — documents go directly in the parent
            folderMap.set(packName, parent.id);
            continue;
        }

        let sub = game.folders.find(
            (f) =>
                f.name === cfg.sub &&
                f.type === cfg.type &&
                f.folder?.id === parent.id
        );
        if (!sub) {
            sub = await Folder.create({
                name: cfg.sub,
                type: cfg.type,
                color: PARENT_COLOR,
                folder: parent.id,
            });
        }

        folderMap.set(packName, sub.id);
    }

    return folderMap;
}

/* ------------------------------------------------------------------ */
/*  Organize — move existing loose documents into folders             */
/* ------------------------------------------------------------------ */

/**
 * For worlds that already imported content without folders.
 * Matches world documents to compendium IDs and batch-moves them.
 */
async function organizeExistingContent() {
    const mod = game.modules.get(MODULE_ID);
    if (!mod) {
        ui.notifications.error("Dread of Zarovich module not found.");
        return;
    }

    ui.notifications.info("Dread of Zarovich: Creating folder structure\u2026");
    const folderMap = await createFolderStructure();

    let moved = 0;
    let errors = 0;

    for (const [packName, cfg] of Object.entries(PACK_FOLDERS)) {
        const packId = `${MODULE_ID}.${packName}`;
        const pack = game.packs.get(packId);
        if (!pack) continue;

        const folderId = folderMap.get(packName);
        const collection = COLLECTIONS[cfg.type]?.();
        if (!collection) continue;

        try {
            const index = await pack.getIndex();
            const compendiumIds = new Set(index.map((e) => e._id));

            // Find world documents whose IDs match the compendium (keepId: true)
            // and that aren't already in the correct folder
            const updates = [];
            for (const doc of collection) {
                if (compendiumIds.has(doc.id) && doc.folder?.id !== folderId) {
                    updates.push({ _id: doc.id, folder: folderId });
                }
            }

            if (updates.length > 0) {
                const cls = pack.documentClass;
                await cls.updateDocuments(updates);
                moved += updates.length;
            }
        } catch (err) {
            console.error(`DoZ Organize: Failed to organize ${packId}`, err);
            errors++;
        }
    }

    await game.settings.set(MODULE_ID, "organized", true);

    if (errors > 0) {
        ui.notifications.warn(
            `Dread of Zarovich: Organized ${moved} documents with ${errors} error(s). Check console.`
        );
    } else {
        ui.notifications.info(
            `Dread of Zarovich: Organized ${moved} documents into folders!`
        );
    }
}

/* ------------------------------------------------------------------ */
/*  Import — fresh install with folder organization                   */
/* ------------------------------------------------------------------ */

/**
 * Import all documents from every compendium pack in this module,
 * placing each into the correct folder.
 */
const COLLECTIONS = {
    Actor: () => game.actors,
    Item: () => game.items,
    JournalEntry: () => game.journal,
    Scene: () => game.scenes,
    RollTable: () => game.tables,
};

async function importAllContent() {
    const mod = game.modules.get(MODULE_ID);
    if (!mod) {
        ui.notifications.error("Dread of Zarovich module not found.");
        return;
    }

    ui.notifications.info("Dread of Zarovich: Creating folder structure\u2026");
    const folderMap = await createFolderStructure();

    // Gather pack IDs from module manifest
    const packIds = mod.packs.map((p) => `${MODULE_ID}.${p.name}`);
    let total = 0;
    let errors = 0;

    ui.notifications.info("Dread of Zarovich: Beginning import\u2026");

    for (const packId of packIds) {
        const pack = game.packs.get(packId);
        if (!pack) {
            console.warn(`DoZ Import: Pack ${packId} not found, skipping.`);
            errors++;
            continue;
        }

        try {
            const documents = await pack.getDocuments();
            if (documents.length === 0) continue;

            const cls = pack.documentClass;
            const packName = pack.metadata.name;
            const folderId = folderMap.get(packName) ?? null;

            const data = documents.map((d) => {
                const obj = d.toObject();
                if (folderId) obj.folder = folderId;
                return obj;
            });

            await cls.createDocuments(data, { keepId: true });
            total += documents.length;

            console.log(
                `DoZ Import: ${pack.metadata.label} — ${documents.length} entries → folder ${folderId}`
            );
        } catch (err) {
            console.error(`DoZ Import: Failed to import ${packId}`, err);
            errors++;
        }
    }

    await game.settings.set(MODULE_ID, "imported", true);
    await game.settings.set(MODULE_ID, "organized", true);

    if (errors > 0) {
        ui.notifications.warn(
            `Dread of Zarovich: Imported ${total} entries with ${errors} pack error(s). Check console for details.`
        );
    } else {
        ui.notifications.info(
            `Dread of Zarovich: Successfully imported ${total} entries into folders!`
        );
    }
}

/* ------------------------------------------------------------------ */
/*  Re-import — delete existing + fresh import from compendium        */
/* ------------------------------------------------------------------ */

/**
 * Delete all previously imported documents (matched by compendium ID)
 * and re-import fresh from the module's compendium packs.
 */
async function reimportAllContent() {
    const mod = game.modules.get(MODULE_ID);
    if (!mod) {
        ui.notifications.error("Dread of Zarovich module not found.");
        return;
    }

    ui.notifications.info("Dread of Zarovich: Preparing re-import\u2026");
    const folderMap = await createFolderStructure();

    const packIds = mod.packs.map((p) => `${MODULE_ID}.${p.name}`);
    let deleted = 0;
    let imported = 0;
    let errors = 0;

    for (const packId of packIds) {
        const pack = game.packs.get(packId);
        if (!pack) {
            console.warn(`DoZ Re-import: Pack ${packId} not found, skipping.`);
            errors++;
            continue;
        }

        try {
            const packName = pack.metadata.name;
            const cfg = PACK_FOLDERS[packName];
            if (!cfg) continue;

            const cls = pack.documentClass;
            const collection = COLLECTIONS[cfg.type]?.();
            if (!collection) continue;

            // Get compendium document IDs
            const index = await pack.getIndex();
            const compendiumIds = new Set(index.map((e) => e._id));

            // Delete existing world documents that match compendium IDs
            const toDelete = collection
                .filter((d) => compendiumIds.has(d.id))
                .map((d) => d.id);

            if (toDelete.length > 0) {
                await cls.deleteDocuments(toDelete);
                deleted += toDelete.length;
                console.log(
                    `DoZ Re-import: Deleted ${toDelete.length} existing entries from ${packName}`
                );
            }

            // Re-import fresh from compendium
            const documents = await pack.getDocuments();
            if (documents.length === 0) continue;

            const folderId = folderMap.get(packName) ?? null;
            const data = documents.map((d) => {
                const obj = d.toObject();
                if (folderId) obj.folder = folderId;
                return obj;
            });

            await cls.createDocuments(data, { keepId: true });
            imported += documents.length;

            console.log(
                `DoZ Re-import: ${pack.metadata.label} — ${documents.length} entries imported`
            );
        } catch (err) {
            console.error(`DoZ Re-import: Failed on ${packId}`, err);
            errors++;
        }
    }

    await game.settings.set(MODULE_ID, "imported", true);
    await game.settings.set(MODULE_ID, "organized", true);

    if (errors > 0) {
        ui.notifications.warn(
            `Dread of Zarovich: Re-imported ${imported} entries (deleted ${deleted}) with ${errors} error(s).`
        );
    } else {
        ui.notifications.info(
            `Dread of Zarovich: Re-imported ${imported} entries (replaced ${deleted} existing). All content is up to date!`
        );
    }
}

/* ------------------------------------------------------------------ */
/*  Settings menu FormApplication — confirmation dialog               */
/* ------------------------------------------------------------------ */

class ReimportFormApplication extends FormApplication {
    static get defaultOptions() {
        return foundry.utils.mergeObject(super.defaultOptions, {
            id: "doz-reimport",
            title: "Dread of Zarovich \u2014 Re-import Content",
            template: `modules/${MODULE_ID}/templates/reimport.html`,
            width: 480,
        });
    }

    /** If template file doesn't exist, render inline */
    async _renderInner(data) {
        try {
            return await super._renderInner(data);
        } catch {
            // Fallback: inline HTML if template missing
            const html = document.createElement("form");
            html.innerHTML = `
                <div style="margin-bottom: 16px;">
                    <p><strong>This will delete and re-import all Dread of Zarovich
                    content</strong> in this world from the module's compendium packs.</p>
                    <p style="color: #ff6644; margin-top: 8px;">
                        <i class="fas fa-exclamation-triangle"></i>
                        Any manual edits you have made to imported actors, items,
                        journals, scenes, or tables will be <strong>overwritten</strong>.
                    </p>
                    <p style="margin-top: 8px;">Use this after updating the module to
                    get the latest NPC stats, items, and other data.</p>
                </div>
                <div style="text-align: center; margin-top: 12px;">
                    <button type="submit" style="padding: 6px 24px;">
                        <i class="fas fa-sync-alt"></i> Re-import &amp; Overwrite All
                    </button>
                </div>
            `;
            return $(html);
        }
    }

    getData() {
        return {};
    }

    async _updateObject(event, formData) {
        await reimportAllContent();
        this.close();
    }
}
