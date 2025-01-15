import { contextBridge, ipcRenderer } from 'electron';

import { BridgeData } from './main/types';

declare global {
  interface Window {
    bridge: {
      refreshData: () => Promise<BridgeData>;
    };
  }
}

contextBridge.exposeInMainWorld('bridge', {
  refreshData: () => ipcRenderer.invoke('refresh-data')
});
