import React from 'react';
import { useQoSStore } from '../store/useQoSStore';
import { Shield, Cpu } from 'lucide-react';

export const TopNav: React.FC = () => {
  const { activeTab, setActiveTab, policies, toggleQoS, connected, useMock, setUseMock } = useQoSStore();

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'flows', label: 'Flows' },
    { id: 'policies', label: 'Policies' },
    { id: 'events', label: 'Events' },
    { id: 'demo', label: 'Demo Mode' },
    { id: 'about', label: 'About & Arch' },
  ] as const;

  return (
    <header className="top-nav">
      {/* Brand Mark */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '28px',
            height: '28px',
            backgroundColor: 'var(--color-primary)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 700,
            fontSize: '14px',
            letterSpacing: '-0.5px',
          }}
        >
          QB
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: '15px', color: 'var(--color-ink)', letterSpacing: '-0.2px' }}>
            QoSBoost
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-ink-subtle)', lineHeight: 1 }}>
            SDN Real-Time Control
          </div>
        </div>
      </div>

      {/* Center Navigation Tabs (DESIGN.md pricing-tab spec) */}
      <nav className="tab-switcher" aria-label="Main Navigation">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            id={`nav-tab-${tab.id}`}
            onClick={() => setActiveTab(tab.id)}
            className={`tab-btn ${activeTab === tab.id ? 'tab-btn-selected' : ''}`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Right Controls: Master QoS Toggle, Connection Status & Mock Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Mock / Live Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setUseMock(!useMock)}
            className="tab-btn"
            style={{
              fontSize: '12px',
              padding: '4px 10px',
              backgroundColor: useMock ? 'var(--color-surface-2)' : 'transparent',
              border: '1px solid var(--color-hairline)',
            }}
            title="Toggle between real Mininet network telemetry and simulated mock data"
          >
            <Cpu size={12} style={{ marginRight: '4px' }} />
            {useMock ? 'Mock Demo Active' : 'Live Network'}
          </button>
        </div>

        {/* Master QoS Switch */}
        <button
          id="btn-master-qos-toggle"
          onClick={toggleQoS}
          className={policies.qos_enabled ? 'btn-primary' : 'btn-secondary'}
          style={{
            padding: '6px 12px',
            fontSize: '13px',
            backgroundColor: policies.qos_enabled ? 'var(--color-primary)' : 'var(--color-surface-2)',
            borderColor: policies.qos_enabled ? 'var(--color-primary)' : 'var(--color-hairline-strong)',
          }}
        >
          <Shield size={14} />
          {policies.qos_enabled ? 'QoS Boost ON' : 'QoS Disabled'}
        </button>

        {/* Connection Status Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: 'var(--color-ink-subtle)',
          }}
          title={connected ? 'Connected to OpenFlow Controller & Backend' : 'Running in Standalone Emulation Mode'}
        >
          <span className={connected || useMock ? 'pulse-dot' : 'pulse-dot-off'} />
          <span>{connected ? 'OF1.3 Live' : useMock ? 'Emulated' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
};
