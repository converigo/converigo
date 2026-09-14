/* Phase 25.x RC-1 behavioural suite (Node, no server required).
 * Run:  node tests/js/globalfmt_rc1.test.mjs
 * Prints a JSON summary on stdout; exits 1 if any case fails. */
import { buildSource } from './globalfmt_rc1_harness.mjs';

/* ----------------------------- DOM stub ---------------------------------- */
class FakeElement {
  constructor(id) { this.id = id; this.style = {}; this.dataset = {}; this.innerHTML = ''; }
}
class FakeSelect extends FakeElement {
  constructor(id) { super(id); this._opts = []; this._value = ''; }
  reset() { this._opts = []; this._value = ''; this.style = {}; this.dataset = {}; this.innerHTML = ''; }
  set innerHTML(html) {
    this._opts = [...String(html).matchAll(/<option value="([^"]*)"/g)].map((m) => m[1]);
    // A real <select> auto-selects its first option when options are replaced.
    this._value = this._opts.length ? this._opts[0] : '';
  }
  get innerHTML() { return this._opts.map((v) => `<option value="${v}">${v}</option>`).join(''); }
  get options() { return this._opts.map((v) => ({ value: v })); }
  get value() { return this._value; }
  set value(v) { this._value = this._opts.includes(v) ? v : ''; }
  // What convertAll() branches on: null while hidden.
  get offsetParent() { return this.style.display === 'none' ? null : {}; }
}

const sel = new FakeSelect('globalFmt');
const label = new FakeElement('footerLabel');
const rowsEl = new FakeElement('rows');
const captured = [];
const changeHandlers = {};

globalThis.window = { translate: (_key, fallback) => fallback };
globalThis.rowsEl = rowsEl;
globalThis.sel = sel;
globalThis.captured = captured;
globalThis.changeHandlers = changeHandlers;
rowsEl.addEventListener = (type, fn) => { changeHandlers[type] = fn; };

globalThis.document = {
  body: { classList: { add() {}, remove() {} } },
  getElementById: (id) => ({ globalFmt: sel, footerLabel: label, rows: rowsEl })[id] || null,
  querySelector: () => null,
  createElement: () => new FakeElement('detached'),
};
globalThis.FormData = class {
  constructor() { this.fields = []; }
  append(key, value) { this.fields.push([key, value && value.name ? `<file:${value.name}>` : String(value)]); }
};
globalThis.fetch = async (url, opts) => {
  if (opts && opts.body instanceof FormData) captured.push({ url: String(url), fields: opts.body.fields });
  return {
    ok: true, status: 201, statusText: 'Created',
    json: async () => ({ conversion_id: 'c-1', download_path: '/download/c-1/out' }),
  };
};

/* --------------------------- load real code ------------------------------ */
new Function(buildSource())();
const H = globalThis.__rc1;

const fileNamed = (name, size = 1024) => ({ name, size, type: 'application/octet-stream' });
const userPicksRowTarget = (jobId, value) =>
  changeHandlers.change({
    target: { closest: () => ({ dataset: { action: 'target', id: jobId }, value }) },
  });
const payloadTargets = () =>
  captured.map((r) => Object.fromEntries(r.fields)).map((f) => f.target_format);
const flush = async () => { for (let i = 0; i < 20; i++) await new Promise((r) => setTimeout(r, 1)); };


/* -------------------------------- cases ---------------------------------- */
const results = [];
function check(name, assertions) {
  const failures = assertions.filter((a) => !a.ok).map((a) => a.message);
  results.push({ name, pass: failures.length === 0, failures });
}
const eq = (actual, expected, label) =>
  ({ ok: actual === expected, message: `${label}: got ${JSON.stringify(actual)}, want ${JSON.stringify(expected)}` });

async function scenario(name, ext, picked) {
  H.reset();
  H.addFiles([fileNamed(`sample.${ext}`)]);
  const seeded = { row: H.jobs[0].target, bulk: sel.value };
  userPicksRowTarget(H.jobs[0].id, picked);
  const displayed = sel.value;   // read before Convert: it clears once no job stays pending
  H.convertAll();
  await flush();
  check(name, [
    eq(displayed, picked, 'displayed #globalFmt'),
    eq(H.jobs[0].target, picked, 'persisted job.target'),
    eq(payloadTargets()[0], picked, 'POST /convert target_format'),
    eq(captured.length, 1, 'request count'),
  ]);
  return seeded;
}

// 1. The seed incident: MP4, user picks MP3.
const mp4Default = await scenario('seed: mp4 + user picks MP3', 'mp4', 'MP3');
check('P1 auto-default policy untouched (mp4 still auto-picks AAC)', [
  eq(mp4Default.row, 'AAC', 'mp4 auto default'),
]);

// 2-4. Other families: image / document / audio.
await scenario('image: jpg + user picks WEBP', 'jpg', 'WEBP');
await scenario('document: pdf + user picks DOCX', 'pdf', 'DOCX');
await scenario('audio: wav + user picks FLAC', 'wav', 'FLAC');

// 5. Consensus across more than one row.
H.reset();
H.addFiles([fileNamed('a.mp4'), fileNamed('b.mp4')]);
userPicksRowTarget(H.jobs[0].id, 'MP3');
userPicksRowTarget(H.jobs[1].id, 'MP3');
const shown5 = sel.value;
H.convertAll();
await flush();
check('two rows agreeing on MP3 -> bulk shows and sends MP3', [
  eq(shown5, 'MP3', 'displayed #globalFmt'),
  eq(JSON.stringify(payloadTargets()), '["MP3","MP3"]', 'payloads'),
]);

// 6. NON-REGRESSION (P6): rows disagree -> selector hidden, each row wins.
H.reset();
H.addFiles([fileNamed('a.mp4'), fileNamed('b.mp4')]);
userPicksRowTarget(H.jobs[0].id, 'MP3');
userPicksRowTarget(H.jobs[1].id, 'WAV');
const hiddenBefore6 = sel.offsetParent === null && sel.style.display === 'none';
H.convertAll();
await flush();
check('rows disagree -> selector hidden, row targets win', [
  { ok: hiddenBefore6, message: `#globalFmt not hidden (display=${JSON.stringify(sel.style.display)})` },
  eq(JSON.stringify(payloadTargets().slice().sort()), '["MP3","WAV"]', 'payloads'),
]);

// 7. Intentional (P5): an explicit bulk-only pick still applies to all rows.
H.reset();
H.addFiles([fileNamed('a.mp4'), fileNamed('b.mp4')]);
userPicksRowTarget(H.jobs[0].id, 'MP3');
userPicksRowTarget(H.jobs[1].id, 'MP3');
sel.value = 'FLAC';                       // user moves only the bulk control
const shown7 = sel.value;
H.convertAll();
await flush();
check('explicit bulk pick still wins (P5 intact)', [
  eq(shown7, 'FLAC', 'displayed #globalFmt'),
  eq(JSON.stringify(payloadTargets()), '["FLAC","FLAC"]', 'payloads'),
]);

// 8. An untouched single row must still show the auto default (no new behaviour).
H.reset();
H.addFiles([fileNamed('a.mp4')]);
check('untouched render still shows the auto default', [eq(sel.value, 'AAC', 'displayed #globalFmt')]);

/* -------------------------------- output --------------------------------- */
const failed = results.filter((r) => !r.pass);
process.stdout.write(JSON.stringify({ ran: results.length, failed: failed.length, results }, null, 2) + '\n');
process.exit(failed.length ? 1 : 0);

