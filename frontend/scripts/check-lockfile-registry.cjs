#!/usr/bin/env node
/**
 * Lockfile Registry Guard
 *
 * Every `resolved` URL in package-lock.json must point at the public npm
 * registry. A local `npm install` behind a private registry mirror (e.g. a
 * corporate npm proxy in ~/.npmrc) writes the mirror's host into any entry it
 * adds or changes, and CI / Firebase builds cannot reach that host.
 *
 * Usage:
 *   node scripts/check-lockfile-registry.cjs          # exit 1 if any foreign host
 *   node scripts/check-lockfile-registry.cjs --fix    # rewrite hosts to npmjs
 *
 * --fix only swaps the origin: mirrors serve identical tarball paths, and the
 * unchanged `integrity` hashes still verify every package on `npm ci`.
 */

const fs = require('fs');
const path = require('path');

const LOCK_PATH = path.join(__dirname, '../package-lock.json');
const REGISTRY = 'https://registry.npmjs.org';

function foreignEntries(lock) {
  return Object.entries(lock.packages || {}).filter(([, pkg]) => {
    const url = pkg.resolved;
    return url && /^https?:\/\//.test(url) && new URL(url).origin !== REGISTRY;
  });
}

function main() {
  const fix = process.argv.includes('--fix');
  const lock = JSON.parse(fs.readFileSync(LOCK_PATH, 'utf8'));
  const foreign = foreignEntries(lock);

  if (foreign.length === 0) {
    console.log('✅ package-lock.json: all resolved URLs use registry.npmjs.org');
    return;
  }

  const hosts = [...new Set(foreign.map(([, pkg]) => new URL(pkg.resolved).origin))];
  if (!fix) {
    console.error(`❌ package-lock.json has ${foreign.length} resolved URL(s) on ${hosts.join(', ')}`);
    console.error('   CI cannot reach private registry mirrors. Fix with:');
    console.error('   cd frontend && node scripts/check-lockfile-registry.cjs --fix');
    process.exit(1);
  }

  for (const [, pkg] of foreign) {
    const url = new URL(pkg.resolved);
    pkg.resolved = REGISTRY + url.pathname + url.search;
  }
  fs.writeFileSync(LOCK_PATH, JSON.stringify(lock, null, 2) + '\n');
  console.log(`🔧 Rewrote ${foreign.length} resolved URL(s) from ${hosts.join(', ')} to ${REGISTRY}`);
}

main();
