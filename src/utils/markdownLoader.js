/**
 * Utility for loading markdown and transcript content
 *
 * Provides lazy-loaded session summaries and strictly published corrected transcripts
 * via deduplicated Vite import.meta.glob maps.
 */

let markdownModules = {};
let transcriptModules = {};

try {
  markdownModules = import.meta.glob('@/assets/sessions/session-*.md', {
    query: '?raw',
    import: 'default',
  });
  transcriptModules = import.meta.glob(
    '@/assets/sessions/transcripts/session_*_corrected.txt',
    {
      query: '?raw',
      import: 'default',
    }
  );
} catch {
  markdownModules = {};
  transcriptModules = {};
}

/**
 * Load a markdown file from the assets/sessions directory
 *
 * @param {string} filename - The filename of the markdown file (e.g., 'session-1.md')
 * @returns {Promise<string>} - The content of the markdown file
 * @throws {Error} - If the file cannot be loaded
 */
export async function loadSessionMarkdown(filename) {
  const modulePath = `/src/assets/sessions/${filename}`;

  if (markdownModules[modulePath]) {
    try {
      const moduleLoader = markdownModules[modulePath];
      return await moduleLoader();
    } catch (error) {
      console.error(`Error loading markdown content for ${filename} via module function:`, error);
      throw new Error(`Failed to load content for markdown file: ${filename}`);
    }
  } else {
    console.error(`Markdown module not found for path: ${modulePath}`);
    console.error('Available modules discovered by import.meta.glob:', Object.keys(markdownModules));
    throw new Error(
      `Markdown file definition not found: ${filename}. Ensure it is located in src/assets/sessions/ and the filename is correct.`
    );
  }
}

/**
 * Load a transcript file from the assets/sessions/transcripts directory
 *
 * @param {string} filename - The filename of the transcript file (e.g., 'session_12_corrected.txt')
 * @returns {Promise<string>} - The content of the transcript file
 * @throws {Error} - If the file cannot be loaded
 */
export async function loadSessionTranscript(filename) {
  const modulePath = `/src/assets/sessions/transcripts/${filename}`;

  if (transcriptModules[modulePath]) {
    try {
      const moduleLoader = transcriptModules[modulePath];
      return await moduleLoader();
    } catch (error) {
      console.error(`Error loading transcript content for ${filename}:`, error);
      throw new Error(`Failed to load content for transcript file: ${filename}`);
    }
  } else {
    console.error(`Transcript module not found for path: ${modulePath}`);
    console.error('Available transcript modules:', Object.keys(transcriptModules));
    throw new Error(
      `Transcript file not found: ${filename}. Ensure it is located in src/assets/sessions/transcripts/.`
    );
  }
}

/**
 * Get the default transcript filename for a session
 * Convention: session-N.md -> session_N_corrected.txt
 *
 * @param {string} sessionId - The session ID (e.g., 'session-12')
 * @returns {string} - The expected transcript filename
 */
export function getTranscriptFilename(sessionId) {
  const sessionNum = sessionId.replace('session-', '');
  return `session_${sessionNum}_corrected.txt`;
}

/**
 * Check if a corrected transcript exists for a given session
 *
 * @param {string} filename - The transcript filename to check
 * @returns {boolean} - Whether the transcript file exists
 */
export function transcriptExists(filename) {
  const modulePath = `/src/assets/sessions/transcripts/${filename}`;
  return Boolean(transcriptModules[modulePath]);
}

/**
 * Check if a session markdown file exists in the assets/sessions directory
 *
 * @param {string} filename - The filename to check
 * @returns {boolean} - Whether the session markdown file exists
 */
export function sessionFileExists(filename) {
  const modulePath = `/src/assets/sessions/${filename}`;
  return Boolean(markdownModules[modulePath]);
}
