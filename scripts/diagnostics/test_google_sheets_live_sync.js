// Playwright test for GoogleSheetsLiveSync component
const { chromium } = require('playwright');

async function testGoogleSheetsLiveSync() {
  console.log('🔍 Starting GoogleSheetsLiveSync Playwright test...\n');
  
  const browser = await chromium.launch({ 
    headless: false, 
    devtools: true 
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Listen for console messages, especially errors
    const consoleMessages = [];
    const errors = [];
    
    page.on('console', msg => {
      const message = {
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      };
      consoleMessages.push(message);
      console.log(`[${msg.type().toUpperCase()}] ${msg.text()}`);
      
      if (msg.type() === 'error') {
        errors.push(message);
      }
    });
    
    page.on('pageerror', error => {
      console.error('🚨 Page Error:', error.message);
      errors.push({
        type: 'pageerror',
        text: error.message,
        stack: error.stack
      });
    });
    
    // Navigate to the application
    console.log('📍 Navigating to application...');
    
    // Try multiple possible URLs
    const possibleUrls = [
      'http://localhost:3001',
      'http://localhost:3000',
      'https://wolf-goat-pig.vercel.app', // common deployment URL pattern
      'https://wgp-app.netlify.app' // another common pattern
    ];
    
    let currentUrl = null;
    for (const url of possibleUrls) {
      try {
        console.log(`Trying ${url}...`);
        await page.goto(url, { waitUntil: 'networkidle', timeout: 10000 });
        currentUrl = url;
        console.log(`✅ Successfully connected to ${url}`);
        break;
      } catch (error) {
        console.log(`❌ Failed to connect to ${url}: ${error.message}`);
      }
    }
    
    if (!currentUrl) {
      console.log('❌ Could not connect to any URL. Please provide the correct URL.');
      return { success: false, errors: ['No accessible URL found'] };
    }
    
    // Wait for page to load
    await page.waitForTimeout(3000);
    
    // Take initial screenshot
    await page.screenshot({ path: 'initial-state.png', fullPage: true });
    console.log('📸 Initial screenshot saved as initial-state.png');
    
    // Check for the GoogleSheetsLiveSync component
    console.log('🔍 Looking for GoogleSheetsLiveSync component...');
    
    // Try to navigate to the Google Sheets sync page
    const navigationOptions = [
      async () => await page.goto(`${currentUrl}/#/sheets-sync`),
      async () => await page.goto(`${currentUrl}/sheets-sync`),
      async () => await page.click('text=Sheets'), // if there's a navigation link
      async () => await page.click('text=Google Sheets'),
      async () => await page.click('text=Sync'),
      async () => {
        // Look for the component directly on the current page
        const component = await page.$('.min-h-screen:has-text("Live Google Sheets Sync")');
        return component !== null;
      }
    ];
    
    let foundComponent = false;
    for (const navOption of navigationOptions) {
      try {
        await navOption();
        await page.waitForTimeout(2000);
        
        // Check if GoogleSheetsLiveSync component is present
        const syncTitle = await page.$('text=Live Google Sheets Sync');
        if (syncTitle) {
          foundComponent = true;
          console.log('✅ Found GoogleSheetsLiveSync component!');
          break;
        }
      } catch (error) {
        // Continue trying other options
      }
    }
    
    if (!foundComponent) {
      console.log('⚠️  GoogleSheetsLiveSync component not found on current page');
      console.log('🔍 Checking page content for any mentions of sheets or sync...');
      
      const pageContent = await page.textContent('body');
      if (pageContent.toLowerCase().includes('sheet') || pageContent.toLowerCase().includes('sync')) {
        console.log('📝 Found sheet/sync related content in page');
      }
      
      // Take a screenshot of what we can see
      await page.screenshot({ path: 'page-content.png', fullPage: true });
      console.log('📸 Page content screenshot saved as page-content.png');
    }
    
    // Test specific functionality if component is found
    if (foundComponent) {
      console.log('🧪 Testing GoogleSheetsLiveSync functionality...');
      
      // Test 1: Check for the specific error about variable 'm'
      console.log('🔍 Checking for variable "m" initialization error...');
      
      const specificErrors = errors.filter(error => 
        error.text.includes('Cannot access') && 
        error.text.includes('before initialization')
      );
      
      if (specificErrors.length > 0) {
        console.log('🚨 Found the reported error!');
        specificErrors.forEach(error => {
          console.log(`Error: ${error.text}`);
          console.log(`Location: ${error.location ? JSON.stringify(error.location) : 'Unknown'}`);
        });
      }
      
      // Test 2: Try interacting with the component
      try {
        // Fill in a test Google Sheets URL
        const urlInput = await page.$('input[placeholder*="spreadsheets"]');
        if (urlInput) {
          console.log('📝 Testing URL input...');
          await urlInput.fill('https://docs.google.com/spreadsheets/d/test-sheet-id/edit#gid=0');
          await page.waitForTimeout(1000);
        }
        
        // Try to click sync button
        const syncButton = await page.$('button:has-text("Sync Now")');
        if (syncButton) {
          console.log('🔄 Testing sync button...');
          await syncButton.click();
          await page.waitForTimeout(2000);
        }
        
        // Check for auto-sync checkbox
        const autoSyncCheckbox = await page.$('input[type="checkbox"]#autoSync');
        if (autoSyncCheckbox) {
          console.log('✅ Testing auto-sync functionality...');
          await autoSyncCheckbox.click();
          await page.waitForTimeout(1000);
        }
        
      } catch (error) {
        console.log(`⚠️  Error during interaction testing: ${error.message}`);
      }
    }
    
    // Wait for any async errors to surface
    console.log('⏱️  Waiting for potential async errors...');
    await page.waitForTimeout(5000);
    
    // Take final screenshot
    await page.screenshot({ path: 'final-state.png', fullPage: true });
    console.log('📸 Final screenshot saved as final-state.png');
    
    // Analyze results
    console.log('\n📊 TEST RESULTS:');
    console.log(`Total console messages: ${consoleMessages.length}`);
    console.log(`Total errors: ${errors.length}`);
    
    if (errors.length > 0) {
      console.log('\n🚨 ERRORS FOUND:');
      errors.forEach((error, index) => {
        console.log(`${index + 1}. [${error.type}] ${error.text}`);
        if (error.location) {
          console.log(`   Location: ${JSON.stringify(error.location)}`);
        }
      });
    }
    
    // Check specifically for the reported error
    const targetError = errors.find(error => 
      error.text.includes('Cannot access') && 
      error.text.includes('before initialization') &&
      error.text.includes('GoogleSheetsLiveSync')
    );
    
    if (targetError) {
      console.log('\n🎯 CONFIRMED: Found the reported "Cannot access \'m\' before initialization" error!');
      console.log('📍 This error is likely caused by the useEffect dependency array referencing performLiveSync before it\'s declared.');
    }
    
    return {
      success: true,
      foundComponent,
      totalConsoleMessages: consoleMessages.length,
      totalErrors: errors.length,
      errors: errors,
      hasTargetError: !!targetError,
      url: currentUrl
    };
    
  } finally {
    await browser.close();
  }
}

// Run the test
testGoogleSheetsLiveSync()
  .then(results => {
    console.log('\n✅ Test completed successfully');
    if (results.hasTargetError) {
      console.log('🔧 RECOMMENDATION: Fix the variable hoisting issue in GoogleSheetsLiveSync.js:24');
    }
  })
  .catch(error => {
    console.error('❌ Test failed:', error);
  });