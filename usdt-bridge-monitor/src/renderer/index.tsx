import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

import { BridgeData } from '../types';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'main' | 'about'>('main');
  const [bridgeData, setBridgeData] = useState<BridgeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Use IPC to request data from the main process
      const data: BridgeData = await window.bridge.refreshData();
      setBridgeData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败，请检查网络或稍后再试');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="container">
      {currentPage === 'main' ? (
        <>
          <h1>USDT Bridge Monitor</h1>
          <div className="volume-display">
            <p className="volume-label">Remaining Bridge Volume:</p>
            {loading ? (
              <div className="loading"></div>
            ) : error ? (
              <p className="error-message">{error}</p>
            ) : (
              <p className="volume-value">
                {bridgeData ? `${bridgeData.remaining_volume} ${bridgeData.currency}` : '加载中...'}
              </p>
            )}
          </div>
          <button 
            className="refresh-button" 
            onClick={fetchData}
            disabled={loading}
          >
            刷新
          </button>
          <button 
            className="about-button"
            onClick={() => setCurrentPage('about')}
          >
            关于
          </button>
        </>
      ) : (
        <div className="about-content">
          <h1>关于</h1>
          <p>USDT Bridge Monitor v1.0</p>
          <p>简单的实时监控工具，获取跨链额度。</p>
          <p>开发团队：XXX</p>
          <button 
            className="refresh-button"
            onClick={() => setCurrentPage('main')}
          >
            返回
          </button>
        </div>
      )}
    </div>
  );
};

const container = document.getElementById('root');
const root = createRoot(container!);
root.render(<App />);
