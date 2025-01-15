import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { fetchBridgeVolume } from './scraper';

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 400,
    height: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, '../preload/preload.js')
    }
  });

  mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));

  // Handle refresh requests from the renderer
  ipcMain.handle('refresh-data', async () => {
    try {
      return await fetchBridgeVolume();
    } catch (error) {
      throw new Error('加载失败，请检查网络或稍后再试');
    }
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});
