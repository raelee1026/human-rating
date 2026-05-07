// ═══════════════════════════════════════════════════════════════
//  Google Apps Script — paste this into your Apps Script project
//
//  Setup:
//  1. Open your Google Sheet
//  2. Extensions → Apps Script
//  3. Delete the default code and paste this entire file
//  4. Save (Ctrl+S)
//  5. Deploy → New deployment → Web app
//     - Execute as: Me
//     - Who has access: Anyone
//  6. Copy the Web App URL into experiment.html → APPS_SCRIPT_URL
// ═══════════════════════════════════════════════════════════════

const HEADERS = [
  'observer',
  'scene',
  'stimulus_A',
  'stimulus_B',
  'response',             // 1 = left preferred, 2 = right preferred
  'selected_condition',
  'timestamp',            // client-side
  'submitted_at',         // server-side
];

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const sheet   = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();

    // Write headers if sheet is empty
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(HEADERS);
      sheet.getRange(1, 1, 1, HEADERS.length)
           .setFontWeight('bold')
           .setBackground('#1a1a2e')
           .setFontColor('#ffffff');
      sheet.setFrozenRows(1);
    }

    const now = new Date().toISOString();

    payload.rows.forEach(row => {
      sheet.appendRow([...row, now]);
    });

    return response({ status: 'ok', rows_written: payload.rows.length });

  } catch (err) {
    return response({ status: 'error', error: err.message });
  }
}

// Handle GET — useful for testing the endpoint is alive
function doGet(e) {
  return response({ status: 'ok', message: 'Apps Script is running' });
}

function response(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
