// Revised history-based data format with connections as history entries
// Expanded with hypothetical Session 1 & 2 events

export const historyBasedDataExpanded = {
    // List of sessions, metadata only
    sessions: [
        {
            id: 'session-0', // Renamed from session-minus-1 for clarity
            title: 'Initial Setup',
            date: '2025-04-02', // Assuming this was setup before Session 1 play
            summary: 'Introduced main characters, key NPCs, items, and initial known connections.'
        },
        {
            id: 'session-1',
            title: 'The Whispering Node',
            date: '2025-04-06', // Date of Session 1 play
            summary: 'Investigated a newly detected Active Node, recovered an Ancient data shard, and skirmished with Kragnor\'s forces.'
        },
        {
            id: 'session-2',
            title: 'Echoes of Convergence',
            date: '2025-04-13', // Date of Session 2 play (hypothetical next week)
            summary: 'Delivered shard to Silverhand, consulted the Oracle of Nexus, received a cryptic prophecy, and encountered Morana Shadowweaver.'
        }
        // ... other sessions
    ],

    // Unified log of all entity creations, updates, and connection changes
    historyEntries: [
        // --- Session: session-0 (Previously session-minus-1) ---
        // (All entries from the previous example go here, but with sessionId: 'session-0')
        // Character: thorne (Creation)
        { entityId: 'thorne', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T10:00:00Z', data: { entityType: 'character', id: 'thorne', name: 'Thorne Ironheart', player: 'Player Name 1', race: 'Dwarf', class: 'Paladin', level: 5, background: 'Relic Hunter', bio: 'Born into a family of traditional relic hunters, Thorne discovered ancient armor in the ruins of Thaumanar that bonded to him, granting him paladin abilities. He seeks to fulfill the Prophecy of Convergence.' } },
        { entityId: 'thorne', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T10:15:00Z', data: { entityType: 'character', connectedEntityType: 'location', connectedEntityId: 'thaumanar', reason: 'Discovered ancient armor...' } },
        { entityId: 'thorne', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T10:16:00Z', data: { entityType: 'character', connectedEntityType: 'location', connectedEntityId: 'oracle-nexus', reason: 'Visited the Oracle...' } },
        { entityId: 'thorne', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T10:17:00Z', data: { entityType: 'character', connectedEntityType: 'npc', connectedEntityId: 'silverhand', reason: 'Silverhand has hired Thorne multiple times...' } },
        // NPC: silverhand (Creation & Connections)
        { entityId: 'silverhand', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T10:30:00Z', data: { entityType: 'npc', id: 'silverhand', name: 'Lord Bartholomew Silverhand', location: 'Spire Central', role: 'High Councilor & Oracle Interpreter', description: 'A distinguished noble descended from the Luminar Dynasty, Silverhand claims partial Ancient bloodline. He leads excavation efforts at Active Nodes and consults regularly with the Oracle of Nexus.', status: 'Ally' } },
        { entityId: 'silverhand', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T10:35:00Z', data: { entityType: 'npc', connectedEntityType: 'location', connectedEntityId: 'spire-central', reason: 'Leads the High Council...' } },
        { entityId: 'silverhand', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T10:36:00Z', data: { entityType: 'npc', connectedEntityType: 'character', connectedEntityId: 'thorne', reason: 'Has hired Thorne...' } },
        { entityId: 'silverhand', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T10:37:00Z', data: { entityType: 'npc', connectedEntityType: 'character', connectedEntityId: 'brom', reason: 'Sees Brom as potentially dangerous...' } },
        { entityId: 'silverhand', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T10:38:00Z', data: { entityType: 'npc', connectedEntityType: 'location', connectedEntityId: 'oracle-nexus', reason: 'Official interpreter...' } },
        { entityId: 'silverhand', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T10:39:00Z', data: { entityType: 'npc', connectedEntityType: 'location', connectedEntityId: 'nexus', reason: 'Maintains a residence...' } },
        // NPC: grimshaw (Creation & Connections)
        { entityId: 'grimshaw', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T11:00:00Z', data: { entityType: 'npc', id: 'grimshaw', name: 'Grimshaw the Merchant', location: 'Traveling between Ancient Sites', role: 'Relic Trader & Member of Blazing Sigil', description: 'A rotund, jovial halfling bearing a faint luminous mark on his palm. Specializes in Ancient relics and Crystal Mind fragments. Rumored to have a collection of working Ethereal Lattice shards.', status: 'Neutral' } },
        { entityId: 'grimshaw', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T11:05:00Z', data: { entityType: 'npc', connectedEntityType: 'character', connectedEntityId: 'zephyr', reason: 'Regular supplier...' } },
        { entityId: 'grimshaw', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T11:06:00Z', data: { entityType: 'npc', connectedEntityType: 'location', connectedEntityId: 'thaumanar', reason: 'Operates a secret shop...' } },
        { entityId: 'grimshaw', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T11:07:00Z', data: { entityType: 'npc', connectedEntityType: 'location', connectedEntityId: 'eternal-flame', reason: 'Uses the Eternal Flame...' } },
        // NPC: morana (Creation & Connections)
        { entityId: 'morana', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T11:30:00Z', data: { entityType: 'npc', id: 'morana', name: 'Morana Shadowweaver', location: 'Regions near Active Nodes', role: 'Voidspeaker Mystic', description: 'A mysterious woman who communes with entities from beyond the Sundering. She claims to hear whispers from the Luminous Concord and warns of the dangers in reactivating Ancient technology.', status: 'Unknown' } },
        { entityId: 'morana', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T11:35:00Z', data: { entityType: 'npc', connectedEntityType: 'location', connectedEntityId: 'crimson-desert', reason: 'Studies the effects...' } },
        { entityId: 'morana', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T11:36:00Z', data: { entityType: 'npc', connectedEntityType: 'character', connectedEntityId: 'lyra', reason: 'Has been teaching Lyra...' } },
        // NPC: kragnor (Creation & Connections)
        { entityId: 'kragnor', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T12:00:00Z', data: { entityType: 'npc', id: 'kragnor', name: 'Kragnor the Merciless', location: 'The Dark Spire', role: 'Warlord & Guardian Subjugator', description: 'A massive orc chieftain who has managed to control Ancient guardians using a modified Crystal Mind. Commands an army enhanced with repurposed Ancient technology from his fortress built around an Active Node.', status: 'Enemy' } },
        { entityId: 'kragnor', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T12:05:00Z', data: { entityType: 'npc', connectedEntityType: 'location', connectedEntityId: 'dark-spire', reason: 'Built a fortress...' } },
        { entityId: 'kragnor', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T12:06:00Z', data: { entityType: 'npc', connectedEntityType: 'character', connectedEntityId: 'zephyr', reason: 'Bitter rival...' } },
        // Locations (Creations)
        { entityId: 'thaumanar', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T13:00:00Z', data: { 
            entityType: 'location', 
            name: 'Thaumanar', 
            type: 'City', 
            subtype: 'magic',
            region: 'Eastern Spire Territory',
            description: 'The first major settlement established after the Restoration, built around the Whispering Spires. Known for its ancient architecture and the Wielders Guild headquarters. The city\'s foundations incorporate Ancient technology that still hums with power.'
        }},
        { entityId: 'oracle-nexus', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T13:01:00Z', data: { 
            entityType: 'location', 
            name: 'Oracle Nexus', 
            type: 'Place of Power',
            subtype: 'monument',
            region: 'Central Confederation',
            description: 'A vast thinking engine of Ancient design that awakens periodically to offer cryptic wisdom. The Great Temple built around it is the center of the Nexus Priesthood\'s power and influence.'
        }},
        { entityId: 'spire-central', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T13:02:00Z', data: { 
            entityType: 'location', 
            name: 'Spire Central', 
            type: 'Government Building',
            subtype: 'capital',
            region: 'Heart of the Confederation',
            description: 'The capital of the Seven Spires Confederation, defined by seven towering Ancient structures that emit protective fields. The High Council chambers sit at the base of the tallest spire, where representatives gather to govern the confederation.'
        }},
        { entityId: 'nexus', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T13:03:00Z', data: { 
            entityType: 'location', 
            name: 'Nexus', 
            type: 'City District',
            subtype: 'capital',
            region: 'Central Confederation',
            description: 'Built around the Oracle temple, Nexus is a city of scholars, priests, and pilgrims. The Nexus Priesthood interprets the Oracle\'s cryptic wisdom, making the city a political and spiritual center of the known world.'
        }},
        { entityId: 'eternal-flame', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T13:04:00Z', data: { 
            entityType: 'location', 
            name: 'Eternal Flame', 
            type: 'Landmark',
            subtype: 'magic',
            region: 'Western Confederation',
            description: 'A massive flame that has burned without fuel since before recorded history. The surrounding city harnesses its heat for industry and comfort. Scholars theorize it may be a controlled breach in the Ethereal Lattice.'
        }},
        { entityId: 'crimson-desert', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T13:05:00Z', data: { 
            entityType: 'location', 
            name: 'Crimson Desert', 
            type: 'Region',
            subtype: 'magic',
            region: 'Far Southern Reaches',
            description: 'The first documented Active Node to awaken in the modern era, transforming the surrounding wasteland into a lush landscape. Ancient mechanisms hum beneath the sands, and strange creatures adapted to the new environment roam the periphery.'
        }},
        { entityId: 'dark-spire', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T13:06:00Z', data: { 
            entityType: 'location', 
            name: 'The Dark Spire', 
            type: 'Fortress',
            subtype: 'fortress',
            region: 'Northern Wastes',
            description: 'A fortress built around an Active Node, where Ancient guardians patrol under the control of a modified Crystal Mind. The surrounding area has been twisted by wild energies, creating dangerous and surreal landscapes.'
        }},
        
        // Adding new locations from the older dataset that weren't in the original history
        { entityId: 'crystal-gardens', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T13:07:00Z', data: { 
            entityType: 'location', 
            name: 'Crystal Gardens of Luminar', 
            type: 'Point of Interest',
            subtype: 'natural',
            region: 'Southern Territories',
            description: 'Vast gardens where crystalline plants grow, emitting gentle light that keeps darkness at bay. Many believe the gardens were once a recreational area for the Ancients, now overgrown and wild after millennia of neglect.'
        }},
        { entityId: 'whisperwood', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T13:08:00Z', data: { 
            entityType: 'location', 
            name: 'Whisperwood Village', 
            type: 'Village',
            subtype: 'natural',
            region: 'Far Eastern Frontier',
            description: 'Once an ordinary settlement, this village was transformed when an Active Node awakened nearby. The forest surrounding it has evolved rapidly, with plants and animals exhibiting unusual properties and intelligence.'
        }},
        
        // Add connections for the new locations
        { entityId: 'crystal-gardens', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T13:10:00Z', data: { entityType: 'location', connectedEntityType: 'character', connectedEntityId: 'zephyr', reason: 'Where Zephyr discovered his Bloodline Channeler abilities while meditating.' }},
        { entityId: 'whisperwood', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T13:11:00Z', data: { entityType: 'location', connectedEntityType: 'character', connectedEntityId: 'lyra', reason: 'Lyra\'s home village, transformed by an Active Node awakening.' }},
        
        // Items (Creations & Connections)
        // Frostbite Blade
        { entityId: 'frostbite-blade', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T14:00:00Z', data: { entityType: 'item', id: 'frostbite-blade', name: 'Frostbite Blade', type: 'Ancient Weapon (Ethereal Edge)', rarity: 'Rare', attunement: 'Required (Bloodline Affinity)', description: 'A longsword that appears to be made of translucent blue ice. Analysis suggests it\'s actually a fragment of the Ethereal Lattice, crystallized during the Sundering. It deals an additional 1d6 cold damage and slows targets by manipulating local temporal flow.', found: 'Recovered from an Active Node in the former Frozen Wastes, now the Crimson Desert', owner: 'Thorne Ironheart' } },
        { entityId: 'frostbite-blade', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T14:05:00Z', data: { entityType: 'item', connectedEntityType: 'character', connectedEntityId: 'thorne', reason: 'Currently wielded...' } },
        { entityId: 'frostbite-blade', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T14:06:00Z', data: { entityType: 'item', connectedEntityType: 'location', connectedEntityId: 'crimson-desert', reason: 'Found in the depths...' } },
        // Amulet of True Sight
        { entityId: 'amulet-of-true-sight', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T14:30:00Z', data: { entityType: 'item', id: 'amulet-of-true-sight', name: 'Amulet of True Sight', type: 'Luminous Concord Relic', rarity: 'Very Rare', attunement: 'Required (Any Wielder)', description: 'This silver amulet contains a fragment of a Celestial Lens from the Age of Wonders. The purple gemstone is actually a compressed data storage unit that interfaces with the wearer\'s visual cortex, allowing perception of invisible entities and the Ethereal Plane remnants.', found: 'Gift from Lord Silverhand after helping secure an Ancient archive', owner: 'Party Treasure' } },
        { entityId: 'amulet-of-true-sight', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T14:35:00Z', data: { entityType: 'item', connectedEntityType: 'npc', connectedEntityId: 'silverhand', reason: 'Silverhand gifted this item...' } },
        // Cloak of Elvenkind
        { entityId: 'cloak-of-elvenkind', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T15:00:00Z', data: { entityType: 'item', id: 'cloak-of-elvenkind', name: 'Cloak of Elvenkind', type: 'Adapted Ancient Technology', rarity: 'Uncommon', attunement: 'Not Required', description: 'This cloak incorporates threads from materials created by the Ancients. It contains microscopic adaptive camouflage nodes that respond to surroundings, granting advantage on Stealth checks and disadvantage to those perceiving the wearer.', found: 'Hidden cache in the Whispering Spires of Thaumanar', owner: 'Lyra Moonshadow' } },
        { entityId: 'cloak-of-elvenkind', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T15:05:00Z', data: { entityType: 'item', connectedEntityType: 'character', connectedEntityId: 'lyra', reason: 'Used by Lyra...' } },
        { entityId: 'cloak-of-elvenkind', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T15:06:00Z', data: { entityType: 'item', connectedEntityType: 'location', connectedEntityId: 'thaumanar', reason: 'Discovered in a hidden cache...' } },
        // Orb of Dragonkind
        { entityId: 'orb-of-dragonkind', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T15:30:00Z', data: { entityType: 'item', id: 'orb-of-dragonkind', name: 'Orb of Dragonkind', type: 'Crystal Mind (Specialized)', rarity: 'Legendary', attunement: 'Required (Bloodline Channeler only)', description: 'One of the legendary Crystal Minds containing Ancient knowledge specific to draconic entities. The Ancients studied and possibly created dragons as guardians. This orb can access those control protocols, but only for red dragons. Contains partial instructions from the Eternity Working that caused the Sundering.', found: 'Kragnor\'s vault in the Dark Spire Active Node', owner: 'Zephyr Stormwind' } },
        { entityId: 'orb-of-dragonkind', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T15:35:00Z', data: { entityType: 'item', connectedEntityType: 'character', connectedEntityId: 'zephyr', reason: 'Target of Zephyr\'s quest...' } },
        { entityId: 'orb-of-dragonkind', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T15:36:00Z', data: { entityType: 'item', connectedEntityType: 'npc', connectedEntityId: 'kragnor', reason: 'Previously owned by Kragnor...' } },
        { entityId: 'orb-of-dragonkind', sessionId: 'session-0', changeType: 'connection_added', timestamp: '2025-04-02T15:37:00Z', data: { entityType: 'item', connectedEntityType: 'location', connectedEntityId: 'dark-spire', reason: 'Recovered from Kragnor\'s vault...' } },
        // Characters (Creations)
        { entityId: 'lyra', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T16:00:00Z', data: { entityType: 'character', name: 'Lyra Moonshadow', class: 'Ranger', player: 'Player Name 2', race: 'Elf', level: 5, background: 'Survivor of Node Awakening', bio: 'Lyra\'s village was transformed when an Active Node awakened nearby. The sudden surge of magical energy changed the surrounding environment and wildlife, giving her a mystical connection to the altered creatures.' } },
        { entityId: 'zephyr', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T16:30:00Z', data: { entityType: 'character', name: 'Zephyr Stormwind', class: 'Sorcerer', player: 'Player Name 3', race: 'Tiefling', level: 5, background: 'Bloodline Channeler', bio: 'Descendant of the Ancients, Zephyr\'s blood resonates with the remnants of the Ethereal Lattice. He possesses one of the rare Crystal Minds and can access fragments of Ancient knowledge through it.' } },
        { entityId: 'brom', sessionId: 'session-0', changeType: 'creation', timestamp: '2025-04-02T17:00:00Z', data: { entityType: 'character', name: 'Brom Stonebeard', class: 'Cleric', player: 'Player Name 4', race: 'Human', level: 5, background: 'Former Oracle Guard', bio: 'Once a dedicated protector of the Oracle of Nexus, Brom left his post after hearing a disturbing prophecy. He now seeks to prevent another Sundering by monitoring the increasing Ancient activity.' } },


        // --- Session: session-1 ---
        { // Silverhand gives the party a quest (connection represents the quest briefing/acceptance)
            entityId: 'silverhand',
            sessionId: 'session-1',
            changeType: 'connection_added',
            timestamp: '2025-04-06T10:00:00Z',
            data: { entityType: 'npc', connectedEntityType: 'character', connectedEntityId: 'thorne', reason: 'Tasked party (via Thorne) to investigate energy readings at the Silent Mire ruins.' } // Assuming party accepts
        },
        { // Create the location for the session if it wasn't known before
            entityId: 'silent-mire-ruins',
            sessionId: 'session-1',
            changeType: 'creation',
            timestamp: '2025-04-06T10:15:00Z',
            data: { entityType: 'location', name: 'Silent Mire Ruins', type: 'Ancient Ruin Site', region: 'Near Thaumanar', description: 'Fog-shrouded ruins known for strange silences and distorted flora.' }
        },
        { // Update location status based on Silverhand's info
            entityId: 'silent-mire-ruins',
            sessionId: 'session-1',
            changeType: 'update',
            timestamp: '2025-04-06T10:30:00Z',
            data: { entityType: 'location', status: 'Suspected Active Node' }
        },
        { // Lyra uses her skills/cloak while scouting the ruins
            entityId: 'lyra',
            sessionId: 'session-1',
            changeType: 'update', // Representing skill usage success or significant action
            timestamp: '2025-04-06T10:45:00Z',
            data: { entityType: 'character', last_action: 'Successfully scouted Silent Mire entrance using stealth.' }
        },
        { // Party discovers the entrance and confirms Node activity
            entityId: 'silent-mire-ruins',
            sessionId: 'session-1',
            changeType: 'update',
            timestamp: '2025-04-06T11:00:00Z',
            data: { entityType: 'location', status: 'Confirmed Active Node', description: 'Entrance to underground facility discovered. Node emits low hum.' }
        },
        { // Encounter with reactivated defenses
            entityId: 'ancient-guardian-smr-1',
            sessionId: 'session-1',
            changeType: 'creation',
            timestamp: '2025-04-06T11:15:00Z',
            data: { entityType: 'creation', name: 'Shimmering Sentry', type: 'Ancient Construct', status: 'Hostile' }
        },
        { // Zephyr uses the Orb of Dragonkind to try and interface/disrupt the construct
            entityId: 'zephyr',
            sessionId: 'session-1',
            changeType: 'update',
            timestamp: '2025-04-06T11:30:00Z',
            data: { entityType: 'character', last_action: 'Attempted to interface with Ancient Guardian using Orb of Dragonkind (Partial Success).' }
        },
        { // Guardian defeated/disabled
            entityId: 'ancient-guardian-smr-1',
            sessionId: 'session-1',
            changeType: 'update',
            timestamp: '2025-04-06T11:45:00Z',
            data: { entityType: 'update', status: 'Disabled' }
        },
        { // Discovery of a key item inside the Node
            entityId: 'lattice-data-shard-smr',
            sessionId: 'session-1',
            changeType: 'creation',
            timestamp: '2025-04-06T12:00:00Z',
            data: { entityType: 'item', name: 'Flickering Data Shard', type: 'Ethereal Lattice Fragment', rarity: 'Rare', description: 'A shard pulsing with faint light, containing fragmented Ancient data.', attunement: 'Requires tech/arcane analysis' }
        },
        { // Party acquires the item
            entityId: 'lattice-data-shard-smr',
            sessionId: 'session-1',
            changeType: 'connection_added',
            timestamp: '2025-04-06T12:15:00Z',
            data: { entityType: 'item', connectedEntityType: 'character', connectedEntityId: 'brom', reason: 'Recovered by Brom (Party Treasure) from the Silent Mire Node.' } // Assigning to someone to hold
        },
        { // Encounter Kragnor's scouts attempting to enter the node
            entityId: 'kragnor-orc-reaver-1',
            sessionId: 'session-1',
            changeType: 'creation',
            timestamp: '2025-04-06T12:30:00Z',
            data: { entityType: 'npc', name: 'Orc Reaver', allegiance: 'Kragnor', status: 'Hostile', equipment: 'Repurposed Ancient Pike' }
        },
        { // Thorne uses Frostbite Blade effectively in combat
            entityId: 'thorne',
            sessionId: 'session-1',
            changeType: 'update',
            timestamp: '2025-04-06T12:45:00Z',
            data: { entityType: 'character', last_action: 'Successfully repelled Kragnor\'s scouts using Frostbite Blade and paladin abilities.' }
        },
        { // Kragnor's forces repelled for now
            entityId: 'kragnor-orc-reaver-1',
            sessionId: 'session-1',
            changeType: 'update',
            timestamp: '2025-04-06T13:00:00Z',
            data: { entityType: 'npc', status: 'Defeated/Fled' }
        },


        // --- Session: session-2 ---
        { // Party delivers the shard to Silverhand
            entityId: 'lattice-data-shard-smr',
            sessionId: 'session-2',
            changeType: 'connection_removed', // Removing from Brom/Party possession
            timestamp: '2025-04-13T10:00:00Z',
            data: { entityType: 'item', connectedEntityType: 'character', connectedEntityId: 'brom', reason: 'Handed over for analysis.' }
        },
        { // Silverhand takes possession
            entityId: 'lattice-data-shard-smr',
            sessionId: 'session-2',
            changeType: 'connection_added',
            timestamp: '2025-04-13T10:15:00Z',
            data: { entityType: 'item', connectedEntityType: 'npc', connectedEntityId: 'silverhand', reason: 'Received from party for analysis.' }
        },
        { // Silverhand analyzes shard and directs party to Oracle (updating existing connection/reason)
            entityId: 'silverhand',
            sessionId: 'session-2',
            changeType: 'connection_updated', // Using a hypothetical update type for connections
            timestamp: '2025-04-13T10:30:00Z',
            data: { entityType: 'npc', connectedEntityType: 'character', connectedEntityId: 'thorne', reason: 'Analyzed shard - contains Lattice resonance patterns. Urges party to consult Oracle of Nexus immediately regarding the Prophecy of Convergence.' }
        },
        { // Party travels to Nexus, encounters Grimshaw
            entityId: 'lyra', // Lyra notices him first?
            sessionId: 'session-2',
            changeType: 'connection_added',
            timestamp: '2025-04-13T10:45:00Z',
            data: { entityType: 'character', connectedEntityType: 'npc', connectedEntityId: 'grimshaw', reason: 'Encountered Grimshaw in Nexus Market. He inquired about "newly activated sources" and offered a strange focusing lens.' }
        },
        { // Zephyr uses bloodline knowledge/Orb connection to sense something about the lens (maybe decline?)
            entityId: 'zephyr',
            sessionId: 'session-2',
            changeType: 'update',
            timestamp: '2025-04-13T11:00:00Z',
            data: { entityType: 'character', last_action: 'Sensed conflicting energies from Grimshaw\'s offered lens; advised caution.' }
        },
        { // Party attempts to consult Oracle - interaction with Priesthood
            entityId: 'nexus-high-priest',
            sessionId: 'session-2',
            changeType: 'creation',
            timestamp: '2025-04-13T11:15:00Z',
            data: { entityType: 'npc', name: 'High Priest Voltan', allegiance: 'Oracle Priesthood', status: 'Neutral', role: 'Guardian of the Oracle Chamber' }
        },
        { // Brom uses religious knowledge/diplomacy (or Silverhand's name) to gain access
            entityId: 'brom',
            sessionId: 'session-2',
            changeType: 'connection_added',
            timestamp: '2025-04-13T11:30:00Z',
            data: { entityType: 'character', connectedEntityType: 'npc', connectedEntityId: 'nexus-high-priest', reason: 'Successfully negotiated access to the Oracle Chamber.' }
        },
        { // The Oracle delivers a prophecy fragment
            entityId: 'prophecy-convergence-fragment-1',
            sessionId: 'session-2',
            changeType: 'creation',
            timestamp: '2025-04-13T11:45:00Z',
            data: {
                entityType: 'lore',
                name: 'Oracle Pronouncement 7B',
                text: '"When the Shard resonates with the Bonded Armor... when the Bloodline grasps the Mind... the Void will speak through the Shadow Weaver... Convergence demands sacrifice or offers oblivion."',
                source: 'Oracle of Nexus'
            }
        },
        { // Party receives the prophecy
            entityId: 'prophecy-convergence-fragment-1',
            sessionId: 'session-2',
            changeType: 'connection_added',
            timestamp: '2025-04-13T12:00:00Z',
            data: { entityType: 'lore', connectedEntityType: 'character', connectedEntityId: 'thorne', reason: 'Received prophecy fragment relevant to the party.' } // Linking to Thorne due to 'Bonded Armor' mention
        },
        { // Encounter with Morana after leaving the Oracle
            entityId: 'lyra',
            sessionId: 'session-2',
            changeType: 'connection_added',
            timestamp: '2025-04-13T12:15:00Z',
            data: { entityType: 'character', connectedEntityType: 'npc', connectedEntityId: 'morana', reason: 'Morana intercepted party near Nexus. Warned against blindly trusting the Oracle ("a machine echo") and Silverhand ("binds himself to failing structures"). Mentioned the Void\'s perspective on Convergence.' }
        },
        { // Update Morana's relationship/status slightly based on the interaction
            entityId: 'morana',
            sessionId: 'session-2',
            changeType: 'update',
            timestamp: '2025-04-13T12:30:00Z',
            data: { entityType: 'npc', status: 'Warning/Concerned', last_known_action: 'Advised party to seek truth beyond Ancient echoes.' }
        },

    ]
};

export default historyBasedDataExpanded;