// Shared avatar and portrait asset loader (single Vite glob per asset directory)

let avatarModules = {};
let portraitModules = {};

try {
  avatarModules = import.meta.glob('@/assets/avatars/avatar/*', {
    eager: true,
    import: 'default',
  });
  portraitModules = import.meta.glob('@/assets/avatars/portrait/*', {
    eager: true,
    import: 'default',
  });
} catch {
  // Running outside Vite (e.g., direct Node verification/scripts)
  avatarModules = {};
  portraitModules = {};
}

const CHARACTER_ALIAS_MAP = {
  berridin: 'berridin',
  nyx: 'nyx',
  ellara: 'ellara',
  ysidor: 'ysidor',
  witty: 'witty',
  'whitaker "witty" whitman vi': 'witty',
  'lord whitaker the 6th': 'witty',
  tsinyra: 'tsinyra',
  "tsi'nyra": 'tsinyra',
  "tsi’nyra": 'tsinyra',
};

function normalizeId(value) {
  if (typeof value !== 'string') return '';
  const trimmed = value.trim().toLowerCase();
  if (!trimmed) return '';
  if (CHARACTER_ALIAS_MAP[trimmed]) return CHARACTER_ALIAS_MAP[trimmed];
  return trimmed.replace(/['’]/g, '');
}

function findAssetUrl(modules, filenameOrId, folder) {
  if (typeof filenameOrId !== 'string' || !filenameOrId.trim()) {
    return null;
  }

  const raw = filenameOrId.trim().toLowerCase();
  const normalized = normalizeId(raw);
  const hasExtension = /\.[a-z0-9]+$/i.test(raw);

  for (const [assetPath, url] of Object.entries(modules)) {
    const lowerPath = assetPath.toLowerCase();
    if (hasExtension && lowerPath.endsWith(`/${raw}`)) {
      return url;
    }
    if (
      lowerPath.includes(`/${folder}/${raw}.`) ||
      (normalized && lowerPath.includes(`/${folder}/${normalized}.`))
    ) {
      return url;
    }
  }

  return null;
}

/**
 * Resolve an avatar image URL by filename (e.g. 'berridin.png') or entity id (e.g. 'berridin').
 * @param {string} filename
 * @returns {string|null}
 */
export function getAvatarUrl(filename) {
  return findAssetUrl(avatarModules, filename, 'avatar');
}

/**
 * Resolve a portrait image URL by filename (e.g. 'ellara.png') or entity id (e.g. 'ellara').
 * @param {string} filename
 * @returns {string|null}
 */
export function getPortraitUrl(filename) {
  return findAssetUrl(portraitModules, filename, 'portrait');
}

/**
 * Resolve a character or NPC avatar URL by entity id or speaker name.
 * @param {string} id
 * @returns {string|null}
 */
export function getCharacterAvatar(id) {
  const normalized = normalizeId(id);
  if (!normalized || normalized === 'gm') return null;
  return findAssetUrl(avatarModules, normalized, 'avatar');
}

/**
 * Resolve a character or NPC portrait URL by entity id or speaker name.
 * @param {string} id
 * @returns {string|null}
 */
export function getCharacterPortrait(id) {
  const normalized = normalizeId(id);
  if (!normalized || normalized === 'gm') return null;
  return findAssetUrl(portraitModules, normalized, 'portrait');
}

export default {
  getAvatarUrl,
  getPortraitUrl,
  getCharacterAvatar,
  getCharacterPortrait,
};
