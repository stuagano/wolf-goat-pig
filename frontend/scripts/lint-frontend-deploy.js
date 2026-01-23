#!/usr/bin/env node
/**
 * Frontend Deployment Linter
 *
 * Pre-commit hook that catches common deployment issues:
 * 1. Service worker syntax errors
 * 2. Missing cache busting for CSS/JS changes
 * 3. Hardcoded URLs that should be environment variables
 * 4. PWA manifest issues
 */

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.join(__dirname, '..');
const PUBLIC_DIR = path.join(ROOT_DIR, 'public');
const SRC_DIR = path.join(ROOT_DIR, 'src');

let warnings = [];
let errors = [];

function warn(msg) {
  warnings.push(`⚠️  ${msg}`);
}

function error(msg) {
  errors.push(`❌ ${msg}`);
}

function info(msg) {
  console.log(`ℹ️  ${msg}`);
}

// Check service worker syntax
function checkServiceWorker() {
  const swPath = path.join(PUBLIC_DIR, 'service-worker.js');

  if (!fs.existsSync(swPath)) {
    warn('service-worker.js not found in public/');
    return;
  }

  const content = fs.readFileSync(swPath, 'utf8');

  // Check for SW_VERSION
  if (!content.includes('SW_VERSION')) {
    error('service-worker.js missing SW_VERSION constant');
  }

  // Check for proper cache naming
  if (!content.includes('CACHE_NAME')) {
    warn('service-worker.js missing CACHE_NAME constant');
  }

  // Check for hardcoded versions (should use variable)
  const hardcodedVersionMatch = content.match(/wgp-cache-v\d+\.\d+\.\d+/);
  if (hardcodedVersionMatch && !content.includes('${SW_VERSION}') && !content.includes('`wgp-cache-v${SW_VERSION}`')) {
    // Only warn if it looks hardcoded
    const cacheNameLine = content.match(/const CACHE_NAME = .*/);
    if (cacheNameLine && !cacheNameLine[0].includes('SW_VERSION')) {
      warn('CACHE_NAME appears to use hardcoded version instead of SW_VERSION variable');
    }
  }

  // Basic syntax check via eval (catches obvious errors)
  try {
    new Function(content);
    info('service-worker.js syntax OK');
  } catch (e) {
    error(`service-worker.js has syntax error: ${e.message}`);
  }
}

// Check for hardcoded URLs in source files
function checkHardcodedUrls() {
  const patterns = [
    /https?:\/\/localhost:\d+/g,
    /https?:\/\/127\.0\.0\.1:\d+/g,
    /https?:\/\/wolf-goat-pig\.onrender\.com/g,
    /https?:\/\/wolf-goat-pig\.vercel\.app/g,
  ];

  const ignoreFiles = ['setupProxy.js', '.env', '.env.example', 'test'];

  function scanDir(dir) {
    if (!fs.existsSync(dir)) return;

    const files = fs.readdirSync(dir, { withFileTypes: true });

    for (const file of files) {
      const filePath = path.join(dir, file.name);

      // Skip node_modules, build, and test files
      if (file.name === 'node_modules' || file.name === 'build' || file.name === 'coverage') {
        continue;
      }

      if (file.isDirectory()) {
        scanDir(filePath);
      } else if (file.name.endsWith('.js') || file.name.endsWith('.jsx') || file.name.endsWith('.ts') || file.name.endsWith('.tsx')) {
        // Skip ignored files
        if (ignoreFiles.some(ignore => filePath.includes(ignore))) {
          continue;
        }

        const content = fs.readFileSync(filePath, 'utf8');

        for (const pattern of patterns) {
          const matches = content.match(pattern);
          if (matches) {
            // Skip if it's in a comment
            const lines = content.split('\n');
            for (let i = 0; i < lines.length; i++) {
              const line = lines[i];
              if (pattern.test(line) && !line.trim().startsWith('//') && !line.trim().startsWith('*')) {
                const relativePath = path.relative(ROOT_DIR, filePath);
                warn(`Hardcoded URL in ${relativePath}:${i + 1} - Use environment variables instead`);
              }
            }
          }
        }
      }
    }
  }

  scanDir(SRC_DIR);
}

// Check manifest.json
function checkManifest() {
  const manifestPath = path.join(PUBLIC_DIR, 'manifest.json');

  if (!fs.existsSync(manifestPath)) {
    warn('manifest.json not found in public/');
    return;
  }

  try {
    const content = fs.readFileSync(manifestPath, 'utf8');
    const manifest = JSON.parse(content);

    // Check required PWA fields
    if (!manifest.name) warn('manifest.json missing "name"');
    if (!manifest.short_name) warn('manifest.json missing "short_name"');
    if (!manifest.icons || manifest.icons.length === 0) warn('manifest.json missing "icons"');
    if (!manifest.start_url) warn('manifest.json missing "start_url"');
    if (!manifest.display) warn('manifest.json missing "display"');

    info('manifest.json structure OK');
  } catch (e) {
    error(`manifest.json parse error: ${e.message}`);
  }
}

// Check version.json exists and is valid
function checkVersionJson() {
  const versionPath = path.join(PUBLIC_DIR, 'version.json');

  if (!fs.existsSync(versionPath)) {
    // This is OK - it gets created during build
    info('version.json will be created during build');
    return;
  }

  try {
    const content = fs.readFileSync(versionPath, 'utf8');
    const version = JSON.parse(content);

    if (!version.version) warn('version.json missing "version" field');
    if (!version.buildTime) warn('version.json missing "buildTime" field');

    info(`version.json current version: ${version.version}`);
  } catch (e) {
    error(`version.json parse error: ${e.message}`);
  }
}

// Main
console.log('🔍 Frontend Deployment Linter\n');

checkServiceWorker();
checkManifest();
checkVersionJson();
checkHardcodedUrls();

console.log('');

if (errors.length > 0) {
  console.log('ERRORS:');
  errors.forEach(e => console.log(`  ${e}`));
  console.log('');
}

if (warnings.length > 0) {
  console.log('WARNINGS:');
  warnings.forEach(w => console.log(`  ${w}`));
  console.log('');
}

if (errors.length === 0 && warnings.length === 0) {
  console.log('✅ All checks passed!\n');
  process.exit(0);
} else if (errors.length > 0) {
  console.log(`❌ ${errors.length} error(s), ${warnings.length} warning(s)\n`);
  process.exit(1);
} else {
  console.log(`⚠️  ${warnings.length} warning(s) - review before deploying\n`);
  process.exit(0);  // Warnings don't block commit
}
