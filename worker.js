// Event 65. Confirm this is the intended event before changing it.
const API_URL = "https://api-bnd.trackify.life/api/bnd/get-seats?event_id=65";
const KV_KEY = "madao_data";
const VERSION = 2;
const API_HEADERS = {
  accept: "application/json",
  origin: "https://ticket.riverflowsinyou.vn",
  referer: "https://ticket.riverflowsinyou.vn/",
  "user-agent": "Mozilla/5.0",
};
const sold = status => status === 3 || status === 4;
const vnTime = ms => new Intl.DateTimeFormat("en-GB", {
  timeZone: "Asia/Ho_Chi_Minh", hour: "2-digit", minute: "2-digit", second: "2-digit",
  day: "2-digit", month: "2-digit", year: "numeric", hourCycle: "h23",
}).format(new Date(ms)).replace(/^(\d{2}\/\d{2}\/\d{4}),?\s+(\d{2}:\d{2}:\d{2})$/, "$2 $1");
const sign = n => `${n > 0 ? "+" : ""}${n}`;
function json(value, status = 200) {
  return new Response(JSON.stringify(value, null, 2), { status, headers: {
    "content-type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*", "Cache-Control": "no-store",
  }});
}
async function sourceResponse() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(API_URL, { headers: API_HEADERS, signal: controller.signal });
    if (!response.ok) throw new Error(`API HTTP ${response.status}`);
    // Read body while timeout is active.
    const text = await response.text();
    return {text, contentType: response.headers.get("content-type") || "application/json"};
  } finally { clearTimeout(timer); }
}
function makeSnapshot(payload) {
  if (!payload || !Array.isArray(payload.result) || payload.result.length === 0) {
    throw new Error("API không có mảng result đầy đủ; giữ nguyên dữ liệu tốt gần nhất.");
  }
  const seatMap = {}, zoneDict = {};
  for (const seat of payload.result) {
    if (seat.code === undefined || seat.code === null || String(seat.code).trim() === "") {
      throw new Error("API có ghế thiếu code.");
    }
    const code = String(seat.code);
    if (Object.hasOwn(seatMap, code)) throw new Error(`API trùng mã ghế: ${code}`);
    const status = Number(seat.status);
    if (![1, 2, 3, 4, 5].includes(status)) throw new Error(`Trạng thái ghế không hợp lệ: ${code}`);
    const zone = typeof seat.ticket_type_name === "string" && seat.ticket_type_name.trim();
    if (!zone) throw new Error(`Ghế thiếu hạng vé: ${code}`);
    if (!Object.hasOwn(zoneDict, zone)) {
      Object.defineProperty(zoneDict, zone, {value: {name: zone, price: seat.price ?? 0,
        total: 0, s1: 0, s2: 0, s3: 0, s4: 0, s5: 0, sold: 0, available: 0}, enumerable: true});
    }
    Object.defineProperty(seatMap, code, {value: {status, zone}, enumerable: true});
    const z = zoneDict[zone]; z.total++; z[`s${status}`]++;
    if (sold(status)) z.sold++;
    if (status === 1) z.available++;
  }
  const zones = Object.values(zoneDict);
  return {seat_map: seatMap, zones,
    total_sold: zones.reduce((n, z) => n + z.sold, 0),
    total_available: zones.reduce((n, z) => n + z.available, 0)};
}
function ensureRoster(oldMap, newMap) {
  const oldCodes = Object.keys(oldMap), newCodes = Object.keys(newMap);
  if (oldCodes.length && (oldCodes.length !== newCodes.length || oldCodes.some(c => !Object.hasOwn(newMap, c)))) {
    throw new Error("Danh sách mã ghế thay đổi/thiếu; cần kiểm tra API hoặc thay đổi sơ đồ, không tự ghi giảm vé.");
  }
}
function zoneSoldCounts(map) {
  const counts = new Map();
  for (const seat of Object.values(map)) {
    if (!counts.has(seat.zone)) counts.set(seat.zone, 0);
    if (sold(Number(seat.status))) counts.set(seat.zone, counts.get(seat.zone) + 1);
  }
  return counts;
}
function salesChanges(oldMap, newMap, time) {
  const changes = [];
  for (const [code, cur] of Object.entries(newMap)) {
    const old = oldMap[code]; if (!old) continue;
    const before = sold(Number(old.status)), after = sold(cur.status);
    if (before && (!after || old.zone !== cur.zone)) changes.push({time, seat: code, zone: old.zone, delta: -1, from: Number(old.status), to: cur.status});
    if (after && (!before || old.zone !== cur.zone)) changes.push({time, seat: code, zone: cur.zone, delta: 1, from: Number(old.status), to: cur.status});
  }
  return changes;
}
function historyDetail(changes) {
  const byZone = new Map();
  for (const c of changes) {
    if (!byZone.has(c.zone)) byZone.set(c.zone, {up: 0, down: 0});
    byZone.get(c.zone)[c.delta > 0 ? "up" : "down"]++;
  }
  return [...byZone].map(([zone, d]) => {
    const net = d.up - d.down;
    return d.up && d.down
      ? `${zone}: +${d.up} / -${d.down} (ròng ${sign(net)})`
      : `${zone}: ${sign(net)}`;
  }).join(" | ");
}
function trackSoldOut(kv, snapshot, now) {
  // Rule v2: sold-out means every seat is status 3 or 4. No waiting period.
  // On migration, old no-available/pending times are not proof of a 3/4 sell-out.
  if (kv.sold_out_rule_version !== 2) {
    if (!kv.sold_out_backup_v1) {
      kv.sold_out_backup_v1 = {
        official: {...(kv.official_sold_out || {})},
        pending: {...(kv.pending_sold_out || {})},
      };
    }
    kv.official_sold_out = {};
    kv.sold_out_rule_version = 2;
  }
  kv.pending_sold_out = {}; // Compatibility with the old response schema only.
  const official = kv.official_sold_out ||= {};
  const conditions = new Map(snapshot.zones.map(z => [z.name, z.total > 0 && z.sold === z.total]));
  const total = snapshot.zones.reduce((n, z) => n + z.total, 0);
  conditions.set("ALL_SHOW", total > 0 && snapshot.total_sold === total);
  for (const key of Object.keys(official)) {
    if (!conditions.get(key)) delete official[key];
  }
  for (const [key, condition] of conditions) {
    if (condition && !Object.hasOwn(official, key)) official[key] = vnTime(now);
  }
}
export async function updateTicketData(env, now = Date.now()) {
  // On validation/network errors: no writes, no false history, no sold-out state changes.
  const {text} = await sourceResponse();
  const snapshot = makeSnapshot(JSON.parse(text));
  const raw = await env.TICKET_KV.get(KV_KEY);
  const kv = raw ? JSON.parse(raw) : {};
  const oldMap = kv.seat_map || {};
  ensureRoster(oldMap, snapshot.seat_map);
  const time = vnTime(now);
  const history = Array.isArray(kv.history) ? kv.history : [];
  const baseline = kv.history_basis_version !== VERSION || !Object.keys(oldMap).length;
  const changes = baseline ? [] : salesChanges(oldMap, snapshot.seat_map, time);
  if (baseline) {
    if (history.length && !kv.history_backup_v1) kv.history_backup_v1 = JSON.parse(JSON.stringify(history));
    // Preserve originals in backup; do not invent zone allocations for old rows.
    kv.history = history.map(row => ({...row,
      detail: String(row.detail || "").startsWith("[Logic cũ]") ? row.detail : `[Logic cũ] ${row.detail || "Chưa đủ dữ liệu đối soát zone"}`}));
    kv.history.unshift({time, sold: snapshot.total_sold, available: snapshot.total_available,
      detail: history.length ? "Mốc chuẩn hóa — đã bán = 3 + 4; không phải vé vừa bán thêm" : "Khởi tạo — số ghế đã chốt tại lần quan sát đầu"});
    kv.history_basis_version = VERSION;
  } else {
    // Independent consistency check: per-zone changes must reconcile to snapshot totals.
    const previousCounts = zoneSoldCounts(oldMap);
    const expectedDelta = snapshot.total_sold - [...previousCounts.values()].reduce((a, b) => a + b, 0);
    if (changes.reduce((n, c) => n + c.delta, 0) !== expectedDelta) throw new Error("Không đối soát được biến động tổng.");
    for (const z of snapshot.zones) {
      const delta = changes.filter(c => c.zone === z.name).reduce((n, c) => n + c.delta, 0);
      if (z.sold - (previousCounts.get(z.name) || 0) !== delta) throw new Error(`Không đối soát được zone ${z.name}`);
    }
    if (changes.length) {
      history.unshift({time, sold: snapshot.total_sold, available: snapshot.total_available, detail: historyDetail(changes)});
    }
    kv.history = history;
  }
  kv.history = kv.history.slice(0, 500);
  kv.sales_log = [...changes, ...(kv.sales_log || [])].slice(0, 5000);
  const newAnomalies = [];
  for (const [code, cur] of Object.entries(snapshot.seat_map)) {
    const oldStatus = oldMap[code]?.status;
    if (oldStatus === undefined || Number(oldStatus) === cur.status) continue;
    const from = Number(oldStatus), to = cur.status;
    const normal = (from === 1 && to === 5) || (from === 5 && to === 3) || (from === 1 && to === 3) || (from === 5 && to === 1);
    if (!normal) newAnomalies.push({time, seat: code, zone: cur.zone, from, to});
  }
  kv.anomaly_log = [...newAnomalies, ...(kv.anomaly_log || [])].slice(0, 500);
  trackSoldOut(kv, snapshot, now);
  // Always update, including polls where only available/payment/hold counts changed.
  Object.assign(kv, snapshot, {last_updated: time, last_updated_at: new Date(now).toISOString()});
  await env.TICKET_KV.put(KV_KEY, JSON.stringify(kv));
  return kv;
}
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, {status: 204, headers: {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, OPTIONS"}});
    if (request.method !== "GET") return json({error: "Method not allowed"}, 405);
    if (url.pathname === "/debug") {
      try {const {text, contentType} = await sourceResponse(); return new Response(text, {headers: {"content-type": contentType, "Cache-Control": "no-store"}});}
      catch (e) {return json({error: String(e.message)}, 502);}
    }
    try {
      const raw = await env.TICKET_KV.get(KV_KEY);
      if (!raw) return json({message: "Đang chờ Cron lấy data lần đầu..."});
      return json({...JSON.parse(raw), last_check: vnTime(Date.now())});
    } catch (e) {return json({error: "Không đọc được dữ liệu KV"}, 500);}
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(updateTicketData(env).catch(error => console.error("Cập nhật vé thất bại; giữ dữ liệu cũ:", error.message)));
  },
};
