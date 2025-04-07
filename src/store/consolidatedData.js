// Revised history-based data format with connections as history entries

// Import the campaign data from the JSON file
import campaignData from '../data/campaignData.json';

// JSON blob for easy copy/paste import/export 
const dataBlob = JSON.stringify(campaignData);

// Parse the JSON blob to create the historyBasedDataExpanded object
export const historyBasedDataExpanded = JSON.parse(dataBlob);

export default historyBasedDataExpanded;
