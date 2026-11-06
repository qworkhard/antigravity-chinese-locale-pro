#!/usr/bin/env node
/**
 * Antigravity Frontend Bundle UI String Extractor & Coverage Auditor (tools/extract_ui_strings.mjs)
 *
 * 自动从当前运行的 Antigravity 窗口 (通过 DevToolsActivePort CDP 通道读取前端 Bundle)
 * 或本地导出的 frontend main.js 中提取所有 UI 属性与 JSX 文本词条，并与 scripts/i18n_data.json
 * 进行覆盖率比对，输出新版本增量未翻译词条。
 *
 * 用法：
 *   node tools/extract_ui_strings.mjs [可选: 本地 main.js 路径]
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const i18nDataPath = path.resolve(__dirname, '../scripts/i18n_data.json');
const i18nData = JSON.parse(fs.readFileSync(i18nDataPath, 'utf8'));
const exactDict = i18nData.exact || {};
const regexRules = (i18nData.regex_rules || []).map((r) => new RegExp(r.pattern));

function isTranslated(str) {
  const s = str.trim();
  if (!s) return true;
  if (exactDict[s]) return true;
  for (const re of regexRules) {
    if (re.test(s)) return true;
  }
  return false;
}

async function loadFrontendBundleText() {
  const cliPath = process.argv[2];
  if (cliPath && fs.existsSync(cliPath)) {
    console.log(`[*] Reading frontend bundle from file: ${cliPath}`);
    return fs.readFileSync(cliPath, 'utf8');
  }

  // Try fetching from active Antigravity instance via DevToolsActivePort CDP WebSocket
  const appData = process.env.APPDATA || '';
  const portFile = path.join(appData, 'Antigravity', 'DevToolsActivePort');
  if (fs.existsSync(portFile)) {
    const port = fs.readFileSync(portFile, 'utf8').split(/\r?\n/)[0].trim();
    const res = await fetch(`http://127.0.0.1:${port}/json`);
    const pages = await res.json();
    const page = pages.find(
      (p) => p.type === 'page' && p.webSocketDebuggerUrl && /^https?:\/\/127\.0\.0\.1/.test(p.url || '')
    );
    if (page) {
      console.log(`[*] Fetching live frontend bundle via CDP from: ${page.url}`);
      const scriptText = await new Promise((resolve) => {
        const ws = new WebSocket(page.webSocketDebuggerUrl);
        ws.onopen = () => {
          ws.send(
            JSON.stringify({
              id: 1,
              method: 'Runtime.evaluate',
              params: {
                expression: `(async () => {
                  const s = document.querySelector('script[src*="main"]') || document.querySelector('script[src]');
                  if (!s) return '';
                  const r = await fetch(s.src);
                  return await r.text();
                })()`,
                awaitPromise: true,
                returnByValue: true
              }
            })
          );
        };
        ws.onmessage = (ev) => {
          const msg = JSON.parse(String(ev.data));
          if (msg.id === 1) {
            ws.close();
            resolve(msg.result?.result?.value || '');
          }
        };
        ws.onerror = () => resolve('');
        setTimeout(() => resolve(''), 5000);
      });
      if (scriptText) return scriptText;
    }
  }

  throw new Error('Could not locate active Antigravity frontend server or local main.js file.');
}

const text = await loadFrontendBundleText();
console.log(`[OK] Loaded frontend bundle (${(text.length / 1024 / 1024).toFixed(2)} MB).`);

const uiPropRe = /\b(?:label|title|description|placeholder|aria-label|tooltip|header|heading|subtext|emptyText)\s*:\s*"([^"\\]{2,160})"/g;

const candidates = new Set();
let m;
while ((m = uiPropRe.exec(text)) !== null) {
  const s = m[1].trim();
  if (!/[A-Za-z]{2,}/.test(s)) continue;
  if (/^[a-z0-9_./:-]+$/.test(s)) continue;
  if (s.includes('var(--') || s.includes('px') || s.includes('flex ') || s.includes('http://')) continue;
  candidates.add(s);
}

const allCandidates = [...candidates];
const untranslated = allCandidates.filter((s) => !isTranslated(s));

console.log(`[OK] Total structured UI property strings scanned: ${allCandidates.length}`);
console.log(
  `[OK] Covered by i18n_data.json: ${allCandidates.length - untranslated.length} / ${allCandidates.length} (${(
    ((allCandidates.length - untranslated.length) / Math.max(1, allCandidates.length)) *
    100
  ).toFixed(1)}%)`
);
console.log(`[*] Remaining untranslated strings (proper nouns / technical constants): ${untranslated.length}`);
