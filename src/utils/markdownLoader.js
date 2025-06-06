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
  // Use import.meta.glob with an alias and the { as: 'raw' } option.
  // The @ alias typically points to the src/ directory.
  const markdownModules = import.meta.glob('@/assets/sessions/*.md', { as: 'raw' });
  
  // Construct the modulePath using the alias, matching the keys generated by import.meta.glob.
  // The keys will be resolved paths, e.g., /src/assets/sessions/filename.md
  const modulePath = `/src/assets/sessions/${filename}`;

  if (markdownModules[modulePath]) {
    try {
      const moduleLoader = markdownModules[modulePath]; // This is an async function that returns a Promise<string>
      const rawMarkdownContent = await moduleLoader();
      return rawMarkdownContent; // When { as: 'raw' }, the module itself is the string content.
    } catch (error) {
      console.error(`Error loading markdown content for ${filename} via module function:`, error);
      throw new Error(`Failed to load content for markdown file: ${filename}`);
    }
  } else {
    console.error(`Markdown module not found for path: ${modulePath}`);
    console.error('Available modules discovered by import.meta.glob:', Object.keys(markdownModules));
    // To help debug, you can log the expected filename and the actual keys
    // console.log('Attempting to load filename:', filename);
    // console.log('Constructed modulePath:', modulePath);
    throw new Error(`Markdown file definition not found: ${filename}. Ensure it is located in src/assets/sessions/ and the filename is correct.`);
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
