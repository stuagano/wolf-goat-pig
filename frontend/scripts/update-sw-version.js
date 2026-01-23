#!/usr/bin/env node
/**
 * Service Worker Version Updater
 *
 * This script automatically updates the SW_VERSION in the service worker file
 * with a timestamp-based version during the build process.
 *
 * Version format: MAJOR.MINOR.BUILD-TIMESTAMP
 * - MAJOR.MINOR: from package.json version
 * - BUILD: auto-incremented or from env
 * - TIMESTAMP: build time in ISO format for cache busting
 */

const fs = require('fs');
const path = require('path');

const SW_PATH = path.join(__dirname, '../public/service-worker.js');
const PACKAGE_PATH = path.join(__dirname, '../package.json');
const VERSION_JSON_PATH = path.join(__dirname, '../public/version.json');

function updateServiceWorkerVersion() {
  // Read package.json for base version
  const packageJson = JSON.parse(fs.readFileSync(PACKAGE_PATH, 'utf8'));
  const baseVersion = packageJson.version || '1.0.0';

  // Generate timestamp for cache busting
  const now = new Date();
  const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const buildNumber = process.env.BUILD_NUMBER || Math.floor(now.getTime() / 1000) % 100000;

  // Create new version string
  const newVersion = `${baseVersion}.${buildNumber}`;

  console.log(`[update-sw-version] Updating service worker version to: ${newVersion}`);

  // Read service worker file
  let swContent = fs.readFileSync(SW_PATH, 'utf8');

  // Update SW_VERSION constant
  const versionRegex = /const SW_VERSION = ['"]([^'"]+)['"]/;
  const match = swContent.match(versionRegex);

  if (match) {
    console.log(`[update-sw-version] Previous version: ${match[1]}`);
    swContent = swContent.replace(versionRegex, `const SW_VERSION = '${newVersion}'`);
    fs.writeFileSync(SW_PATH, swContent, 'utf8');
    console.log(`[update-sw-version] Service worker updated successfully`);
  } else {
    console.error('[update-sw-version] Could not find SW_VERSION in service worker file');
    process.exit(1);
  }

  // Create/update version.json for runtime version checking
  const versionInfo = {
    version: newVersion,
    baseVersion: baseVersion,
    buildNumber: buildNumber,
    buildTime: now.toISOString(),
    timestamp: timestamp
  };

  fs.writeFileSync(VERSION_JSON_PATH, JSON.stringify(versionInfo, null, 2), 'utf8');
  console.log(`[update-sw-version] Created version.json`);

  return versionInfo;
}

// Run if executed directly
if (require.main === module) {
  try {
    const versionInfo = updateServiceWorkerVersion();
    console.log('[update-sw-version] Version info:', JSON.stringify(versionInfo, null, 2));
  } catch (error) {
    console.error('[update-sw-version] Error:', error.message);
    process.exit(1);
  }
}

module.exports = { updateServiceWorkerVersion };
