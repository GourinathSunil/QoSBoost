import React, { useEffect, useRef } from 'react';
import { useQoSStore } from './store/useQoSStore';
import { TopNav } from './components/TopNav';
import { OverviewPage } from './pages/OverviewPage';
import { FlowsPage } from './pages/FlowsPage';
import { PoliciesPage } from './pages/PoliciesPage';
import { EventsPage } from './pages/EventsPage';
import { DemoPage } from './pages/DemoPage';
import { AboutPage } from './pages/AboutPage';

export const App: React.FC = () => {
  const { activeTab, fetchData, setTelemetry, useMock, setUseMock, isLoading, errorMessage, dismissError } = useQoSStore();
  const wsRef = useRef<WebSocket | null>(null);

  // Initial REST fetch & WebSocket connection
  useEffect(() => {
    fetchData();

    // Setup native WebSocket with reconnect
    const connectWS = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          useQoSStore.setState({ connected: true });
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setTelemetry(data);
          } catch (e) {
            console.error('Error parsing WS message', e);
          }
        };

        ws.onclose = () => {
          useQoSStore.setState({ connected: false });
          // If in live mode, attempt reconnect after 3 seconds
          if (!useQoSStore.getState().useMock) {
            setTimeout(connectWS, 3000);
          }
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        useQoSStore.setState({ connected: false });
      }
    };

    if (!useMock) {
      connectWS();
    } else {
      setUseMock(true);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [fetchData, setTelemetry, useMock, setUseMock]);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
      {/* Top Loading Progress Line */}
      {isLoading && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '2px',
            backgroundColor: 'var(--color-primary)',
            zIndex: 9999,
            animation: 'pulse 1.5s infinite',
          }}
        />
      )}

      {/* Top Navigation */}
      <TopNav />

      {/* Dismissible Error Banner */}
      {errorMessage && (
        <div
          style={{
            backgroundColor: 'rgba(229, 72, 77, 0.15)',
            borderBottom: '1px solid rgba(229, 72, 77, 0.3)',
            padding: '10px 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '13px',
            color: '#e5484d',
          }}
        >
          <span>{errorMessage}</span>
          <button
            onClick={dismissError}
            style={{
              background: 'none',
              border: 'none',
              color: '#e5484d',
              cursor: 'pointer',
              fontWeight: 600,
              padding: '2px 8px',
            }}
          >
            ✕ Dismiss
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main style={{ flex: 1, maxWidth: '1280px', width: '100%', margin: '0 auto', padding: 'var(--space-xl) var(--space-lg)' }}>
        {activeTab === 'overview' && <OverviewPage />}
        {activeTab === 'flows' && <FlowsPage />}
        {activeTab === 'policies' && <PoliciesPage />}
        {activeTab === 'events' && <EventsPage />}
        {activeTab === 'demo' && <DemoPage />}
        {activeTab === 'about' && <AboutPage />}
      </main>

      {/* Footer (DESIGN.md footer spec: canvas bg, caption type, hairline top) */}
      <footer
        style={{
          borderTop: '1px solid var(--color-hairline)',
          backgroundColor: 'var(--color-canvas)',
          padding: '32px var(--space-xl)',
          color: 'var(--color-ink-subtle)',
          fontSize: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--color-ink)', fontWeight: 500 }}>QoSBoost</span>
          <span>•</span>
          <span>SDN-Based QoS Management for Real-Time Applications</span>
        </div>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span>OpenFlow 1.3</span>
          <span>Open vSwitch HTB</span>
          <span>Ryu Controller</span>
          <span>FastAPI</span>
          <span>Linear Design System</span>
        </div>
      </footer>
    </div>
  );
};
