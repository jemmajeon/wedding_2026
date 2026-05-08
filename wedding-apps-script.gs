// ====================================================
// Wedding Dashboard — Apps Script Web App
// 결혼 준비 대시보드용 데이터 API
// ====================================================

const WEDDING_SHEET_ID  = '1ovPyDUAsS3yq9xw3r1NAjSNqjV2Bz6b5_BHjgms3jIM';
const HONEYMOON_SHEET_ID = '1nmbZgOjqGVgeq24JMTlF1LjK9s4XtgYD8ro7MAMcvmE';

function doGet(e) {
  try {
    const result = {
      checklist:    getChecklist(),
      budget:       getBudget(),
      reservations: getReservations()
    };
    return ContentService
      .createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ─── 헤더 키워드로 시트(탭) 탐색 ───────────────────
function findSheetByKeywords(ss, keywords) {
  for (const sheet of ss.getSheets()) {
    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();
    if (lastRow === 0 || lastCol === 0) continue;
    const probe = sheet.getRange(1, 1, Math.min(lastRow, 20), Math.min(lastCol, 30))
                        .getValues().flat().map(String);
    if (keywords.every(k => probe.some(v => v.includes(k)))) return sheet;
  }
  return null;
}

// ─── 체크리스트 ──────────────────────────────────────
function getChecklist() {
  const ss    = SpreadsheetApp.openById(WEDDING_SHEET_ID);
  const sheet = findSheetByKeywords(ss, ['완료여부', '실제예정일']);
  if (!sheet) {
    const names = ss.getSheets().map(s => s.getName());
    return { error: '체크리스트 탭을 찾을 수 없음. 탭 목록: ' + names.join(', ') };
  }

  const data = sheet.getDataRange().getValues();

  // 헤더 행 위치 탐색
  let hRow = -1;
  for (let i = 0; i < data.length; i++) {
    if (data[i].map(String).some(c => c === '완료여부')) { hRow = i; break; }
  }
  if (hRow === -1) return { error: '완료여부 헤더를 찾을 수 없음' };

  const hdrs     = data[hRow].map(String);
  const catIdx   = hdrs.indexOf('대분류');
  const subIdx   = hdrs.indexOf('중분류');
  const detIdx   = hdrs.indexOf('소분류');
  const doneIdx  = hdrs.indexOf('완료여부');
  const dueIdx   = hdrs.indexOf('실제예정일');

  const items = [];
  for (let i = hRow + 1; i < data.length; i++) {
    const row = data[i];
    const cat = String(row[catIdx] ?? '').trim();
    if (!cat) continue;

    const rawDue = row[dueIdx];
    let dueDate = '';
    if (rawDue instanceof Date && !isNaN(rawDue)) {
      dueDate = Utilities.formatDate(rawDue, 'Asia/Seoul', 'yyyy-MM-dd');
    } else if (rawDue) {
      dueDate = String(rawDue).trim();
    }

    items.push({
      category: cat,
      sub:      String(row[subIdx] ?? '').trim(),
      detail:   String(row[detIdx] ?? '').trim(),
      done:     String(row[doneIdx] ?? '').trim(),
      dueDate
    });
  }

  const total     = items.length;
  const doneCount = items.filter(it => it.done === '완료').length;

  const byCategory = {};
  for (const it of items) {
    if (!byCategory[it.category]) byCategory[it.category] = { total: 0, done: 0 };
    byCategory[it.category].total++;
    if (it.done === '완료') byCategory[it.category].done++;
  }

  return { total, done: doneCount, byCategory };
}

// ─── 예산 ────────────────────────────────────────────
function getBudget() {
  const ss    = SpreadsheetApp.openById(WEDDING_SHEET_ID);
  // 예산 요약 탭: 대분류 + 최종 예산 키워드로 찾기
  const sheet = findSheetByKeywords(ss, ['대분류', '최종 예산']);
  if (!sheet) return { error: '예산 탭을 찾을 수 없음' };

  const data = sheet.getDataRange().getValues();

  let hRow = -1;
  for (let i = 0; i < data.length; i++) {
    if (data[i].map(String).some(c => c.includes('최종 예산'))) { hRow = i; break; }
  }
  if (hRow === -1) return { error: '예산 헤더를 찾을 수 없음' };

  const hdrs     = data[hRow].map(String);
  const catIdx   = hdrs.findIndex(h => h.includes('대분류'));
  const planIdx  = hdrs.findIndex(h => h.includes('최종 예산'));
  const jiIdx    = hdrs.findIndex(h => h.includes('지혜') && h.includes('금액'));
  const opIdx    = hdrs.findIndex(h => h.includes('오빠') && h.includes('금액'));

  const byCategory = {};
  for (let i = hRow + 1; i < data.length; i++) {
    const row = data[i];
    const cat = String(row[catIdx] ?? '').trim();
    // 빈 셀·총계 행 건너뜀
    if (!cat || cat.includes('총계') || cat.includes('SUM')) continue;

    const plan   = Number(row[planIdx]) || 0;
    const actual = (Number(row[jiIdx]) || 0) + (Number(row[opIdx]) || 0);

    if (!byCategory[cat]) byCategory[cat] = { plan: 0, actual: 0 };
    byCategory[cat].plan   += plan;
    byCategory[cat].actual += actual;
  }

  return { byCategory };
}

// ─── 신혼여행 예약 ───────────────────────────────────
function getReservations() {
  const ss    = SpreadsheetApp.openById(HONEYMOON_SHEET_ID);
  const sheet = ss.getSheetByName('Reservations') ?? ss.getSheets()[0];

  const data    = sheet.getDataRange().getValues();
  const hdrs    = data[0].map(String);
  const dateIdx   = hdrs.indexOf('trip_date');
  const nameIdx   = hdrs.indexOf('name');
  const leadIdx   = hdrs.indexOf('lead_days');
  const urlIdx    = hdrs.indexOf('url');
  const sourceIdx = hdrs.indexOf('source');
  const bookedIdx = hdrs.indexOf('booked');

  const today = new Date();
  const items = [];

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (!row[dateIdx]) continue;

    const tripDate = new Date(row[dateIdx]);
    const lead     = Number(row[leadIdx]) || 0;
    const deadline = new Date(tripDate);
    deadline.setDate(deadline.getDate() - lead);

    const daysLeft = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
    const booked   = row[bookedIdx] === true || String(row[bookedIdx]).toUpperCase() === 'TRUE';

    items.push({
      tripDate:    Utilities.formatDate(tripDate, 'Asia/Seoul', 'yyyy-MM-dd'),
      name:        String(row[nameIdx] ?? ''),
      lead,
      url:         String(row[urlIdx] ?? ''),
      source:      String(row[sourceIdx] ?? ''),
      booked,
      deadline:    Utilities.formatDate(deadline, 'Asia/Seoul', 'yyyy-MM-dd'),
      daysLeft
    });
  }

  // 예약 마감 임박순 정렬
  items.sort((a, b) => a.daysLeft - b.daysLeft);
  return { items };
}
