import puppeteer, { ElementHandle } from 'puppeteer';
import { BridgeData } from '../types';

export async function fetchBridgeVolume(): Promise<BridgeData> {
  let browser;
  try {
    console.log('Launching browser...');
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
      timeout: 10000
    });

    const page = await browser.newPage();
    console.log('Browser launched and page created');
    
    // Set shorter timeouts for better performance
    page.setDefaultTimeout(2000);
    
    // Navigate to the bridge page
    console.log('Navigating to bridge.sui.io...');
    const startTime = Date.now();
    await page.goto('https://bridge.sui.io/', { 
      waitUntil: 'domcontentloaded', // Use faster page load strategy
      timeout: 2000 
    });
    console.log(`Page loaded in ${(Date.now() - startTime)/1000}s`);
    
    // Enable request interception for performance logging
    await page.setRequestInterception(true);
    page.on('request', request => {
      console.log(`Request: ${request.url()}`);
      request.continue();
    });
    page.on('response', response => {
      console.log(`Response: ${response.url()} - ${response.status()}`);
    });
    
    // Wait for and click "I agree" button
    console.log('Looking for "I agree" button...');
    await page.waitForSelector('button', { timeout: 5000 });
    const buttons = await page.$$eval('button', buttons => 
      buttons.map(button => button.textContent)
    );
    console.log('Found buttons:', buttons);
    
    // Find and click the "I agree" button by its text content
    const agreeButton = await page.$$eval('button', (buttons) =>
      buttons.findIndex((button) => button.textContent?.trim() === 'I agree')
    );
    if (agreeButton === -1) {
      throw new Error('Could not find I agree button');
    }
    await page.evaluate((index) => {
      (document.querySelectorAll('button')[index] as HTMLElement).click();
    }, agreeButton);
    console.log('Clicked I agree button');
    
    // Wait for and click the token selector (ETH)
    console.log('Looking for ETH selector...');
    await page.waitForFunction(() => {
      const elements = Array.from(document.querySelectorAll('button, div[role="button"], div[role="combobox"]'));
      const elementDetails = elements.map(el => ({
        tag: el.tagName,
        text: el.textContent?.trim(),
        role: el.getAttribute('role')
      }));
      console.log('Found elements:', JSON.stringify(elementDetails, null, 2));
      return elements.some(el => el.textContent?.trim() === 'ETH');
    }, { timeout: 5000 });
    
    await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('button, div[role="button"], div[role="combobox"]'));
      const ethElement = elements.find(el => el.textContent?.trim() === 'ETH');
      if (ethElement) {
        (ethElement as HTMLElement).click();
      } else {
        throw new Error('Could not find ETH element');
      }
    });
    console.log('Clicked ETH selector');
    
    // Use a more targeted approach to find and click USDT
    console.log('Looking for USDT option...');
    
    // Wait for the token select dropdown
    await page.waitForSelector('select', { timeout: 5000 });
    
    // Find and click the token selector to open dropdown
    await page.evaluate(() => {
      const select = document.querySelector('select');
      if (select) {
        // Find the USDT option
        const usdtOption = Array.from(select.options).find(option => 
          option.textContent?.trim() === 'USDT'
        );
        
        if (usdtOption) {
          console.log('Found USDT option:', {
            index: usdtOption.index,
            value: usdtOption.value,
            text: usdtOption.textContent
          });
          
          // Select USDT
          select.selectedIndex = usdtOption.index;
          select.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
          throw new Error('Could not find USDT option in select');
        }
      } else {
        throw new Error('Could not find token select element');
      }
    });
    
    // Wait for UI to update after token selection
    await page.waitForTimeout(2000);
    console.log('Selected USDT option');
    
    // Wait for any animations to complete
    await page.waitForTimeout(1000);
    
    // Click the switch button (looking for a button that changes direction)
    console.log('Looking for switch button...');
    
    // Take a screenshot to debug the page state
    await page.screenshot({ path: 'switch-button-debug.png' });
    
    // Log all buttons and their properties
    const buttonDetails = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button, [role="button"]')).map(el => ({
        tag: el.tagName,
        text: el.textContent?.trim(),
        classes: el.className,
        role: el.getAttribute('role'),
        ariaLabel: el.getAttribute('aria-label'),
        title: el.getAttribute('title'),
        rect: el.getBoundingClientRect()
      }));
    });
    console.log('Available buttons:', JSON.stringify(buttonDetails, null, 2));
    
    // Try to find the switch button by looking for the swap icon image
    const switchButton = await page.evaluate(() => {
      // Find the swap icon image
      const swapIcon = document.querySelector('img[src*="swap.51800e9f.svg"]');
      if (!swapIcon) {
        console.log('Could not find swap icon image');
        return false;
      }

      // Find the closest button ancestor
      const button = swapIcon.closest('button, [role="button"]');
      if (!button) {
        console.log('Found swap icon but no button ancestor');
        return false;
      }

      console.log('Found switch button:', {
        tag: button.tagName,
        text: button.textContent?.trim(),
        classes: button.className,
        rect: button.getBoundingClientRect()
      });

      (button as HTMLElement).click();
      return true;
    });
    
    if (!switchButton) {
      throw new Error('Could not find switch button');
    }
    console.log('Clicked switch button');
    
    // Wait for and extract the USDT amount
    console.log('Looking for USDT amount...');
    
    // Wait longer for animations and content updates
    console.log('Waiting for content to update...');
    await page.waitForTimeout(5000);
    
    // Take a screenshot before extraction attempt
    await page.screenshot({ path: 'pre-extraction.png' });
    
    // Take a screenshot for debugging
    await page.screenshot({ path: 'volume-debug.png' });
    
    // Log the complete page structure
    console.log('Current page structure:');
    await page.evaluate(() => {
      const logElement = (el: Element, depth = 0) => {
        const indent = ' '.repeat(depth * 2);
        const text = el.textContent?.trim() || '';
        console.log(`${indent}${el.tagName} ${el.className ? `class="${el.className}"` : ''} ${text ? `text="${text}"` : ''}`);
        Array.from(el.children).forEach(child => logElement(child, depth + 1));
      };
      logElement(document.body);
    });
    
    // Look for any numeric value followed by USDT using MutationObserver
    const result = await page.evaluate(() => {
      return new Promise<string | null>((resolve) => {
        // First try to find the value immediately
        const findUSDTAmount = () => {
          const elements = Array.from(document.querySelectorAll('*'));
          for (const el of elements) {
            const text = el.textContent?.trim() || '';
            const match = text.match(/([\d,\.]+)\s*USDT/);
            if (match) {
              console.log('Found USDT amount:', {
                element: {
                  tag: el.tagName,
                  classes: el.className,
                  text: text,
                  path: generateElementPath(el)
                },
                amount: match[1]
              });
              return match[1].replace(/,/g, '');
            }
          }
          return null;
        };

        // Helper function to generate element path
        const generateElementPath = (element: Element): string => {
          const path: string[] = [];
          let current = element;
          while (current && current !== document.body) {
            const parent = current.parentElement;
            if (!parent) break;
            const index = Array.from(parent.children).indexOf(current);
            path.unshift(`${current.tagName}:nth-child(${index + 1})`);
            current = parent;
          }
          return path.join(' > ');
        };

        // Try to find the value immediately
        const immediate = findUSDTAmount();
        if (immediate) {
          resolve(immediate);
          return;
        }

        // If not found, set up an observer
        const observer = new MutationObserver((mutations) => {
          const result = findUSDTAmount();
          if (result) {
            observer.disconnect();
            resolve(result);
          }
        });

        observer.observe(document.body, {
          childList: true,
          subtree: true,
          characterData: true,
          attributes: true
        });

        // Set a timeout to stop observing
        setTimeout(() => {
          observer.disconnect();
          resolve(null);
        }, 5000);
      });
    });
    
    if (!result) {
      // Log all text content for debugging
      const allText = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('*'))
          .map(el => ({
            text: el.textContent?.trim(),
            tag: el.tagName,
            classes: el.className,
            id: el.id,
            path: (() => {
              const path = [];
              let current = el;
              while (current && current !== document.body) {
                const parent = current.parentElement;
                if (!parent) break;
                const index = Array.from(parent.children).indexOf(current);
                path.unshift(`${current.tagName}:nth-child(${index + 1})`);
                current = parent;
              }
              return path.join(' > ');
            })()
          }))
          .filter(item => item.text);
      });
      console.log('All text content:', JSON.stringify(allText, null, 2));
      throw new Error('Could not find USDT amount');
    }
    
    console.log('Successfully extracted volume:', result);
    
    console.log('Successfully extracted volume:', result);
    return {
      remaining_volume: result,
      currency: 'USDT'
    };
  } catch (error) {
    console.error('Scraping failed:', error instanceof Error ? error.message : 'Unknown error');
    throw new Error('加载失败，请检查网络或稍后再试');
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}
