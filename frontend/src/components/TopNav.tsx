import React, { useState } from 'react';
import { useQoSStore } from '../store/useQoSStore';
import { Shield, Cpu, Server, Network, Wifi, ChevronDown, CheckCircle2, AlertCircle } from 'lucide-react';

export const TopNav: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    policies,
    toggleQoS,
    connected,
    connectionStatus,
    useMock,
    setUseMock,
  } = useQoSStore();

  const [showStatusPopover, setShowStatusPopover] = useState(false);

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'flows', label: 'Flows' },
    { id: 'policies', label: 'Policies' },
    { id: 'events', label: 'Events' },
    { id: 'demo', label: 'Demo Mode' },
    { id: 'about', label: 'About & Arch' },
  ] as const;

  const handleKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === 'ArrowRight') {
      const nextIndex = (index + 1) % tabs.length;
      setActiveTab(tabs[nextIndex].id);
      document.getElementById(`nav-tab-${tabs[nextIndex].id}`)?.focus();
    } else if (e.key === 'ArrowLeft') {
      const prevIndex = (index - 1 + tabs.length) % tabs.length;
      setActiveTab(tabs[prevIndex].id);
      document.getElementById(`nav-tab-${tabs[prevIndex].id}`)?.focus();
    } else if (e.key === 'Home') {
      setActiveTab(tabs[0].id);
      document.getElementById(`nav-tab-${tabs[0].id}`)?.focus();
    } else if (e.key === 'End') {
      setActiveTab(tabs[tabs.length - 1].id);
      document.getElementById(`nav-tab-${tabs[tabs.length - 1].id}`)?.focus();
    }
  };

  return (
    <header className="top-nav" role="banner">
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
          aria-hidden="true"
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

      {/* Center Navigation Tabs (DESIGN.md pricing-tab spec with keyboard accessibility) */}
      <nav className="tab-switcher" aria-label="Main Navigation" role="tablist">
        {tabs.map((tab, idx) => {
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              id={`nav-tab-${tab.id}`}
              role="tab"
              aria-selected={isSelected}
              tabIndex={isSelected ? 0 : -1}
              onClick={() => setActiveTab(tab.id)}
              onKeyDown={(e) => handleKeyDown(e, idx)}
              className={`tab-btn ${isSelected ? 'tab-btn-selected' : ''}`}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Right Controls: Master QoS Toggle, Connection Status & Mock Switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Mock / Live Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            id="btn-toggle-mock"
            onClick={() => setUseMock(!useMock)}
            className="tab-btn"
            style={{
              fontSize: '12px',
              padding: '4px 10px',
              backgroundColor: useMock ? 'var(--color-surface-2)' : 'transparent',
              border: '1px solid var(--color-hairline)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '5px',
            }}
            title="Toggle between real Mininet network telemetry and simulated mock data"
          >
            <Cpu size={12} />
            <span>{useMock ? 'Mock Demo Active' : 'Live Network'}</span>
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
          title={policies.qos_enabled ? 'QoS is active on HTB queues' : 'QoS bypassed (FIFO drop-tail)'}
        >
          <Shield size={14} />
          {policies.qos_enabled ? 'QoS Boost ON' : 'QoS Disabled'}
        </button>

        {/* 3-Tier Connection Status Indicator (Backend / Controller / Mininet) */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowStatusPopover(!showStatusPopover)}
            style={{
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-hairline)',
              borderRadius: 'var(--radius-pill)',
              padding: '4px 10px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '12px',
              color: 'var(--color-ink)',
            }}
            aria-expanded={showStatusPopover}
            aria-label="Network System Health Status"
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span
                className={connectionStatus.backend || useMock ? 'pulse-dot' : 'pulse-dot-off'}
                title="Backend API"
              />
              <span
                className={connectionStatus.controller || useMock ? 'pulse-dot' : 'pulse-dot-off'}
                title="Ryu Controller"
              />
              <span
                className={connectionStatus.mininet || useMock ? 'pulse-dot' : 'pulse-dot-off'}
                title="Mininet Data Plane"
              />
            </div>
            <span style={{ color: 'var(--color-ink-subtle)', fontSize: '11px' }}>
              {connected ? 'OF1.3 Live' : useMock ? 'Mock Emulated' : 'Offline'}
            </span>
            <ChevronDown size={11} style={{ color: 'var(--color-ink-subtle)' }} />
          </button>

          {/* Detailed Connection Popover */}
          {showStatusPopover && (
            <div
              style={{
                position: 'absolute',
                top: 'calc(100% + 8px)',
                right: 0,
                width: '280px',
                backgroundColor: 'var(--color-surface-2)',
                border: '1px solid var(--color-hairline-strong)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.6)',
                padding: '16px',
                zIndex: 100,
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-ink)', marginBottom: '12px' }}>
                System Connectivity
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '12px' }}>
                {/* 1. FastAPI Backend */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Server size={13} style={{ color: 'var(--color-primary)' }} />
                    <span style={{ color: 'var(--color-ink-muted)' }}>Backend (FastAPI)</span>
                  </div>
                  <span className="badge" style={{ fontSize: '10px' }}>
                    {connectionStatus.backend ? (
                      <span style={{ color: 'var(--color-semantic-success)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <CheckCircle2 size={10} /> Port 8000
                      </span>
                    ) : useMock ? (
                      <span style={{ color: 'var(--color-brand-secure)' }}>Mock Virtual</span>
                    ) : (
                      <span style={{ color: '#e5484d', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <AlertCircle size={10} /> Disconnected
                      </span>
                    )}
                  </span>
                </div>

                {/* 2. Ryu Controller */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Wifi size={13} style={{ color: 'var(--color-primary)' }} />
                    <span style={{ color: 'var(--color-ink-muted)' }}>Controller (Ryu)</span>
                  </div>
                  <span className="badge" style={{ fontSize: '10px' }}>
                    {connectionStatus.controller ? (
                      <span style={{ color: 'var(--color-semantic-success)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <CheckCircle2 size={10} /> OF1.3 Port 6653
                      </span>
                    ) : useMock ? (
                      <span style={{ color: 'var(--color-brand-secure)' }}>Simulated</span>
                    ) : (
                      <span style={{ color: '#e5484d', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <AlertCircle size={10} /> Offline
                      </span>
                    )}
                  </span>
                </div>

                {/* 3. Mininet Data Plane */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Network size={13} style={{ color: 'var(--color-primary)' }} />
                    <span style={{ color: 'var(--color-ink-muted)' }}>Mininet / OVS</span>
                  </div>
                  <span className="badge" style={{ fontSize: '10px' }}>
                    {connectionStatus.mininet ? (
                      <span style={{ color: 'var(--color-semantic-success)', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <CheckCircle2 size={10} /> HTB Q0-Q3
                      </span>
                    ) : useMock ? (
                      <span style={{ color: 'var(--color-brand-secure)' }}>Synthetic Data</span>
                    ) : (
                      <span style={{ color: '#e5484d', display: 'flex', alignItems: 'center', gap: '3px' }}>
                        <AlertCircle size={10} /> Offline
                      </span>
                    )}
                  </span>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--color-hairline)', marginTop: '12px', paddingTop: '10px', fontSize: '11px', color: 'var(--color-ink-subtle)' }}>
                {useMock
                  ? 'Mock mode active: Synthetic traffic patterns emulate link saturation and packet drops.'
                  : connected
                  ? 'Direct WebSocket connection established with live Ryu OpenFlow telemetry.'
                  : 'Start backend with `python backend/main.py` or switch to Mock Demo mode.'}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
