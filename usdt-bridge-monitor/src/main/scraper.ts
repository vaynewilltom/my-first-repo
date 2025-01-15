import puppeteer, { ElementHandle } from 'puppeteer';
import { BridgeData } from '../types';

export async function fetchBridgeVolume(): Promise<BridgeData> {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    
    // Set timeout to ensure response within 2 seconds
    page.setDefaultTimeout(2000);
    
    // Navigate to the bridge page using HTTPS
    await page.goto('https://bridge.sui.io/', { 
      waitUntil: 'networkidle0',
      timeout: 2000 
    });
    
    // Click "I agree" button
    await page.waitForSelector('button:has-text("I agree")', { timeout: 2000 });
    await page.click('button:has-text("I agree")');
    
    // Wait for and click the token selector (ETH)
    await page.waitForSelector('div[role="button"]:has-text("ETH")', { timeout: 2000 });
    await page.click('div[role="button"]:has-text("ETH")');
    
    // Select USDT option
    await page.waitForSelector('div[role="option"]:has-text("USDT")', { timeout: 2000 });
    await page.click('div[role="option"]:has-text("USDT")');
    
    // Click the switch button to change direction
    await page.waitForSelector('button.switch-button', { timeout: 2000 });
    await page.click('button.switch-button');
    
    // Wait for and extract the remaining bridge volume
    await page.waitForSelector('text/Remaining Bridge Volume', { timeout: 2000 });
    const volumeElement = await page.$('div:has-text("Remaining Bridge Volume")');
    
    if (!volumeElement) {
      throw new Error('加载失败，请检查网络或稍后再试');
    }
    
    const volumeText = await volumeElement.evaluate((el: Element) => el.textContent);
    
    if (!volumeText) {
      throw new Error('加载失败，请检查网络或稍后再试');
    }
    
    // Extract the numeric value and currency
    const match = volumeText.match(/~([\d.]+)\s*USDT/);
    if (!match) {
      throw new Error('加载失败，请检查网络或稍后再试');
    }
    
    return {
      remaining_volume: match[1],
      currency: 'USDT'
    };
  } catch (error) {
    throw new Error('加载失败，请检查网络或稍后再试');
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}
