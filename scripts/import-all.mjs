/**
 * Dread of Zarovich — One-click import for all compendium content.
 *
 * On first activation, presents the GM with a dialog to import all
 * 110 entries across 14 packs into the world.
 */

const MODULE_ID = "dh2e-dread-of-zarovich";

Hooks.once("init", () => {
    game.settings.register(MODULE_ID, "imported", {
        name: "Content Imported",
        hint: "Whether the module content has been imported into this world.",
        scope: "world",
        config: false,
        type: Boolean,
        default: false,
    });
});

Hooks.once("ready", async () => {
    if (!game.user.isGM) return;

    const imported = game.settings.get(MODULE_ID, "imported");
    if (imported) return;

    new Dialog({
        title: "Dread of Zarovich — Import Campaign Content",
        content: `
            <div style="margin-bottom: 12px;">
                <p>Import all <strong>Dread of Zarovich</strong> campaign content into this world?</p>
                <p>This will create <strong>110 entries</strong> across 14 compendium packs:</p>
                <ul style="columns: 2; margin-top: 4px; font-size: 12px;">
                    <li>6 Major NPCs</li>
                    <li>8 Enemy stat blocks</li>
                    <li>8 Weapons</li>
                    <li>4 Armour sets</li>
                    <li>13 Gear &amp; Relics</li>
                    <li>4 Ammunition types</li>
                    <li>6 Mission Objectives</li>
                    <li>5 Campaign Traits</li>
                    <li>7 Player Handouts</li>
                    <li>11 Location entries</li>
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
                },
            },
        },
        default: "import",
    }).render(true);
});

/**
 * Import all documents from every compendium pack in this module.
 */
async function importAllContent() {
    const mod = game.modules.get(MODULE_ID);
    if (!mod) {
        ui.notifications.error("Dread of Zarovich module not found.");
        return;
    }

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
            const data = documents.map((d) => d.toObject());

            await cls.createDocuments(data, { keepId: true });
            total += documents.length;

            console.log(`DoZ Import: ${pack.metadata.label} — ${documents.length} entries`);
        } catch (err) {
            console.error(`DoZ Import: Failed to import ${packId}`, err);
            errors++;
        }
    }

    await game.settings.set(MODULE_ID, "imported", true);

    if (errors > 0) {
        ui.notifications.warn(
            `Dread of Zarovich: Imported ${total} entries with ${errors} pack error(s). Check console for details.`
        );
    } else {
        ui.notifications.info(
            `Dread of Zarovich: Successfully imported ${total} entries!`
        );
    }
}
