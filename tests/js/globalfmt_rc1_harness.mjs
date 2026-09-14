/* Phase 25.x RC-1 harness.
 *
 * Loads the REAL homepage target-selection code out of
 * app/templates/main/converigo_main.html (nothing is re-typed here, so the
 * test cannot pass against a copy that drifted from the template) and runs it
 * against a minimal DOM stub in Node.
 *
 * Fidelity of the stub (deliberately narrow - only what the sliced code uses):
 *   <select>: option re-population resets value to the first option, an
 *             unmatched assignment clears value, offsetParent is null while
 *             display === 'none' (what convertAll() actually branches on).
 *   render(): reduced to buildGlobalFmt(), which is exactly how the real
 *             render() ends; #rows markup is not modelled, so convertAll()'s
 *             row lookup resolves to `job.target` - the same value a real row
 *             <select> would report.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const TEMPLATE = join(
  dirname(fileURLToPath(import.meta.url)), '..', '..',
  'app', 'templates', 'main', 'converigo_main.html',
);

/** Balanced-delimiter slice starting at `anchor`, skipping strings/comments. */
function sliceFrom(src, anchor, open = '{', close = '}') {
  const start = src.indexOf(anchor);
  if (start === -1) throw new Error(`anchor not found: ${anchor}`);
  let i = src.indexOf(open, start);
  if (i === -1) throw new Error(`no '${open}' after anchor: ${anchor}`);
  let depth = 0, state = 'code';
  for (; i < src.length; i++) {
    const c = src[i], n = src[i + 1];
    if (state === 'code') {
      if (c === '/' && n === '/') { state = 'line'; i++; continue; }
      if (c === '/' && n === '*') { state = 'block'; i++; continue; }
      if (c === "'" || c === '"') { state = c; continue; }
      if (c === '`') { state = 'tpl'; continue; }
      if (c === open) depth++;
      else if (c === close) { depth--; if (depth === 0) return src.slice(src.indexOf(open, start), i + 1); }
    } else if (state === 'line' && c === '\n') state = 'code';
    else if (state === 'block' && c === '*' && n === '/') { state = 'code'; i++; }
    else if (state === "'" && c === '\\') i++;
    else if (state === "'" && c === "'") state = 'code';
    else if (state === '"' && c === '\\') i++;
    else if (state === '"' && c === '"') state = 'code';
    else if (state === 'tpl' && c === '\\') i++;
    else if (state === 'tpl' && c === '`') state = 'code';
  }
  throw new Error(`unbalanced slice from anchor: ${anchor}`);
}

function constObject(src, name) {
  const body = sliceFrom(src, `const ${name} = {`);
  return `const ${name} = ${body};\n`;
}

function func(src, name) {
  const decl = `function ${name}(`;
  let start = src.indexOf(decl);
  if (start === -1) throw new Error(`function not found in template: ${name}`);
  // Keep a preceding `async ` modifier - the slice must remain valid syntax.
  if (src.slice(Math.max(0, start - 6), start) === 'async ') start -= 6;
  const braceStart = src.indexOf('{', start + decl.length + (src[start] === 'a' ? 6 : 0));
  const body = sliceFrom(src.slice(braceStart), '{');
  return src.slice(start, braceStart) + body + '\n';
}

export function buildSource() {
  const src = readFileSync(TEMPLATE, 'utf-8');
  const mustContain = (needle) => {
    if (!src.includes(needle)) throw new Error(`template no longer contains: ${needle}`);
  };
  // Guard: if these anchors move, the slices below silently test the wrong code.
  mustContain('function buildGlobalFmt()');
  mustContain('function convertAll()');
  mustContain("addEventListener('change'");
  if (!process.env.RC1_ALLOW_PREFIX) {
    // Only the revert fixture (tests/test_phase25_rc1_globalfmt_consensus.py,
    // layer 3) opts out, so it can demonstrate the assertions - not the guard -
    // are what catch the bug.
    mustContain('const consensus = pendingTargets[0];');   // the RC-1 fix
  }

  const listenerStart = src.indexOf("document.getElementById('rows').addEventListener('change'");
  const listenerEnd = src.indexOf("});", listenerStart);
  if (listenerStart === -1 || listenerEnd === -1) throw new Error("rows 'change' listener not found");
  const listener = src.slice(listenerStart, listenerEnd + 3);
  if (!listener.includes("el.dataset.action==='target'") || !listener.trimEnd().endsWith('});')) {
    throw new Error('row target change listener not sliced correctly');
  }

  return [
    constObject(src, 'STATIC_TARGET_MAP'),
    constObject(src, 'CATEGORY'),
    'let jobs = [];\nlet uid = 0;\n',
    func(src, 'splitName'),
    func(src, 'getValidTargets'),
    func(src, 'categoryOf'),
    func(src, 'addFiles'),
    func(src, 'conversionErrorMessage'),
    func(src, 'conversionDownloadPath'),
    func(src, 'convertJob'),
    func(src, 'buildGlobalFmt'),
    func(src, 'convertAll'),
    'function render(){ buildGlobalFmt(); }\n',
    'function toast(){}\n',
    listener.replace(
      "document.getElementById('rows').addEventListener('change'",
      "rowsEl.addEventListener('change'",
    ),
    `globalThis.__rc1 = {
       addFiles, buildGlobalFmt, convertAll, rows: rowsEl, sel, changeHandlers,
       captured, get jobs(){ return jobs; },
       reset(){ jobs = []; uid = 0; captured.length = 0; sel.reset(); },
     };`,
  ].join('\n');
}
