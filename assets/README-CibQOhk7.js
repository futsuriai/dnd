const n=`# Session Summaries

This directory contains markdown files with detailed summaries of each D&D session.

## File Naming Convention

Files should be named according to the session ID:
- \`session-minus-1.md\` - Initial world building session
- \`session-0.md\` - Character creation session
- \`session-1.md\`, \`session-2.md\`, etc. - Regular campaign sessions

## Adding a New Session Summary

1. Create a new markdown file in this directory following the naming convention
2. Add the session details in markdown format (see examples in existing files)
3. Update the sessions.js file to include a \`summaryFile\` property with the filename

## Format Guidelines

Each session summary should include:

- A heading with the session title
- Date and location information
- Key sections with appropriate subheadings
- Use markdown formatting for better readability:
  - \`**bold**\` for emphasis
  - \`---\` for section dividers
  - Headings with \`#\`, \`##\`, \`###\`

## Example Structure

\`\`\`markdown
## Session X: Title

**Date:** Month Day, Year
**Location:** Location Name

**Opening Scene:**
Description of the opening scene...

---

**Key Event 1:**
Details about the event...

---

**Key Event 2:**
Details about the event...
\`\`\`

## Referencing Characters and Locations

When referencing characters, locations, or other important elements from the campaign, 
you can use standard markdown links or the custom \`[[Name]]\` syntax which will be 
processed by the application to link to the appropriate entity.
`;export{n as default};
