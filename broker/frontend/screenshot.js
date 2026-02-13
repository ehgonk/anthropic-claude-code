import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function takeScreenshot() {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();

  // Set viewport to match typical desktop size
  await page.setViewport({
    width: 1920,
    height: 1080,
  });

  console.log('Navigating to http://localhost:5173...');
  try {
    await page.goto('http://localhost:5173', {
      waitUntil: 'networkidle2',
      timeout: 30000,
    });

    // Wait a bit for chart to render
    await page.waitForTimeout(2000);

    const screenshotPath = join(__dirname, 'screenshot.png');
    await page.screenshot({
      path: screenshotPath,
      fullPage: false,
    });

    console.log(`Screenshot saved to: ${screenshotPath}`);
  } catch (error) {
    console.error('Error taking screenshot:', error.message);
  } finally {
    await browser.close();
  }
}

takeScreenshot();
