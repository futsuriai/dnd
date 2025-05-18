/**
 * Utility for loading markdown content
 * 
 * This utility provides a function to load markdown files from the assets directory
 * using Vite's dynamic import capabilities.
 */

/**
 * Load a markdown file from the assets/sessions directory
 * 
 * @param {string} filename - The filename of the markdown file (e.g., 'session-1.md')
 * @returns {Promise<string>} - The content of the markdown file
 * @throws {Error} - If the file cannot be loaded
 */
export async function loadSessionMarkdown(filename) {
  try {
    // Use dynamic import with ?raw suffix to load markdown as text
    const module = await import(`../assets/sessions/${filename}?raw`);
    return module.default;
  } catch (error) {
    console.error(`Error loading markdown file ${filename}:`, error);
    throw new Error(`Failed to load markdown file: ${filename}`);
  }
}

/**
 * Check if a file exists in the assets/sessions directory
 * This is a helper function for development purposes.
 * 
 * @param {string} filename - The filename to check
 * @returns {boolean} - Whether the file exists (always returns true in production)
 */
export function sessionFileExists(filename) {
  // In a real environment, we'd check if the file exists
  // but for Vite/webpack bundling, this is not straightforward
  // Instead, we rely on error handling in the loadSessionMarkdown function
  return true;
}
