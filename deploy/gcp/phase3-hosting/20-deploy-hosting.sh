#!/usr/bin/env bash
# Deploy frontend/build to Firebase Hosting via the REST API.
# Avoids firebase-tools / npm CI flakes. Requires:
#   - gcloud auth as a project owner (or Hosting Admin)
#   - a production SPA already built in frontend/build (VITE_API_URL baked in)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"

require_cmd gcloud
require_cmd node
require_config GCP_PROJECT_ID FIREBASE_SITE

ROOT="${REPO_ROOT:-$(cd "${GCP_DIR}/../.." && pwd)}/frontend/build"
[[ -f "${ROOT}/index.html" ]] || die "missing ${ROOT}/index.html — build the SPA first"

export PROJECT="${GCP_PROJECT_ID}"
export SITE="${FIREBASE_SITE}"
export TOKEN
TOKEN="$(gc auth print-access-token)"
export ROOT

node <<'NODE'
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const zlib = require('zlib');
const https = require('https');
const { URL } = require('url');

const PROJECT = process.env.PROJECT;
const SITE = process.env.SITE;
const TOKEN = process.env.TOKEN;
const ROOT = process.env.ROOT;

function req(method, urlStr, body, headers = {}, { quota = true } = {}) {
  return new Promise((resolve, reject) => {
    const u = new URL(urlStr);
    const h = { Authorization: `Bearer ${TOKEN}`, ...headers };
    if (quota) h['x-goog-user-project'] = PROJECT;
    if (body) h['Content-Length'] = Buffer.byteLength(body);
    const r = https.request(
      { method, hostname: u.hostname, path: u.pathname + u.search, headers: h },
      (res) => {
        const chunks = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => {
          const text = Buffer.concat(chunks).toString('utf8');
          if (res.statusCode >= 400) {
            reject(new Error(`${method} ${urlStr} -> ${res.statusCode}: ${text}`));
            return;
          }
          resolve(text ? JSON.parse(text) : {});
        });
      },
    );
    r.on('error', reject);
    if (body) r.write(body);
    r.end();
  });
}

function walk(dir, out = []) {
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

function ctypeFor(rel) {
  if (rel.endsWith('.html')) return 'text/html; charset=utf-8';
  if (rel.endsWith('.js')) return 'application/javascript; charset=utf-8';
  if (rel.endsWith('.css')) return 'text/css; charset=utf-8';
  if (rel.endsWith('.json') || rel.endsWith('.map')) return 'application/json';
  if (rel.endsWith('.svg')) return 'image/svg+xml';
  if (rel.endsWith('.png')) return 'image/png';
  if (rel.endsWith('.ico')) return 'image/x-icon';
  if (rel.endsWith('.txt') || rel.endsWith('.md')) return 'text/plain; charset=utf-8';
  if (rel.endsWith('.woff2')) return 'font/woff2';
  if (rel.endsWith('.woff')) return 'font/woff';
  return 'application/octet-stream';
}

(async () => {
  const version = await req(
    'POST',
    `https://firebasehosting.googleapis.com/v1beta1/projects/${PROJECT}/sites/${SITE}/versions`,
    Buffer.from(
      JSON.stringify({
        config: {
          rewrites: [{ glob: '**', path: '/index.html' }],
          headers: [
            {
              glob: '/static/**',
              headers: { 'Cache-Control': 'public, max-age=31536000, immutable' },
            },
          ],
        },
      }),
    ),
    { 'Content-Type': 'application/json' },
  );
  const versionName = version.name;
  console.log('version:', versionName);

  const files = {};
  const byHash = {};
  for (const filePath of walk(ROOT)) {
    const rel = '/' + path.relative(ROOT, filePath).split(path.sep).join('/');
    const raw = fs.readFileSync(filePath);
    const gz = zlib.gzipSync(raw, { level: 9 });
    const digest = crypto.createHash('sha256').update(gz).digest('hex');
    files[rel] = digest;
    byHash[digest] = { gz, ctype: ctypeFor(rel), rel };
  }
  console.log('files:', Object.keys(files).length);

  const pop = await req(
    'POST',
    `https://firebasehosting.googleapis.com/v1beta1/${versionName}:populateFiles`,
    Buffer.from(JSON.stringify({ files })),
    { 'Content-Type': 'application/json' },
  );
  const toUpload = pop.uploadRequiredHashes || [];
  console.log('need upload:', toUpload.length);
  for (let i = 0; i < toUpload.length; i++) {
    const h = toUpload[i];
    const { gz, ctype, rel } = byHash[h];
    const url = `${pop.uploadUrl}/${h}`;
    try {
      await req('POST', url, gz, { 'Content-Type': ctype }, { quota: false });
    } catch (e1) {
      const boundary = '----firebase' + Date.now();
      const multipart = Buffer.concat([
        Buffer.from(
          `--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${path.basename(rel)}"\r\nContent-Type: ${ctype}\r\n\r\n`,
        ),
        gz,
        Buffer.from(`\r\n--${boundary}--\r\n`),
      ]);
      await req(
        'POST',
        url,
        multipart,
        { 'Content-Type': `multipart/form-data; boundary=${boundary}` },
        { quota: false },
      );
    }
    if ((i + 1) % 25 === 0 || i + 1 === toUpload.length) {
      console.log(`uploaded ${i + 1}/${toUpload.length}`);
    }
  }

  await req(
    'PATCH',
    `https://firebasehosting.googleapis.com/v1beta1/${versionName}?updateMask=status`,
    Buffer.from(JSON.stringify({ status: 'FINALIZED' })),
    { 'Content-Type': 'application/json' },
  );
  const release = await req(
    'POST',
    `https://firebasehosting.googleapis.com/v1beta1/projects/${PROJECT}/sites/${SITE}/releases?versionName=${encodeURIComponent(versionName)}`,
    Buffer.from('{}'),
    { 'Content-Type': 'application/json' },
  );
  console.log('release:', release.name);
  console.log(`Live: https://${SITE}.web.app`);
})().catch((e) => {
  console.error(e.message || e);
  process.exit(1);
});
NODE
