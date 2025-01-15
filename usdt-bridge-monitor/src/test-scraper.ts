import { fetchBridgeVolume } from './main/scraper';

async function testScraper() {
  console.log('Starting USDT Bridge volume test...');
  const startTime = Date.now();
  
  try {
    const result = await fetchBridgeVolume();
    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;
    
    console.log('Test Results:');
    console.log('-------------');
    console.log(`Response Time: ${duration}s`);
    console.log(`Remaining Volume: ${result.remaining_volume} ${result.currency}`);
    console.log(`Success: Data fetched successfully`);
    
    if (duration > 2) {
      console.warn('Warning: Response time exceeded 2 second target');
    }
  } catch (error: unknown) {
    if (error instanceof Error) {
      console.error('Test Failed:', error.message);
    } else {
      console.error('Test Failed: Unknown error occurred');
    }
  }
}

testScraper();
