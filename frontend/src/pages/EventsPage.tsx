import React from 'react';
import { useQoSStore } from '../store/useQoSStore';
import { ShieldAlert, Cpu, GitFork, Sliders, CheckCircle } from 'lucide-react';

export const EventsPage: React.FC = () => {
  const { events } = useQoSStore();

  const getEventBadge = (type: string) => {
    switch (type) {
      case 'ADAPTATION':
        return { label: 'Adaptation', color: '#f76b15', bg: 'rgba(247, 107, 21, 0.15)', icon: Sliders };
      case 'METER_DROP':
        return { label: 'Meter Drop', color: '#e5484d', bg: 'rgba(229, 72, 77, 0.15)', icon: ShieldAlert };
      case 'REROUTE':
        return { label: 'QoS Reroute', color: 'var(--color-primary)', bg: 'rgba(94, 106, 210, 0.15)', icon: GitFork };
      case 'ADMISSION':
        return { label: 'Admission', color: 'var(--color-semantic-success)', bg: 'rgba(39, 166, 68, 0.15)', icon: CheckCircle };
      default:
        return { label: type, color: 'var(--color-ink-muted)', bg: 'var(--color-surface-2)', icon: Cpu };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Header */}
      <div>
        <h1 className="headline">SDN Event Audit Log</h1>
        <p className="subhead" style={{ fontSize: '15px', marginTop: '4px' }}>
          Real-time chronological timeline of dynamic queue adjustments, meter drops, admission gating, and routing updates
        </p>
      </div>

      {/* Events List Container */}
      <div className="card-panel" style={{ padding: 0, overflow: 'hidden' }}>
        {events.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: 'var(--color-ink-subtle)' }}>
            No audit events recorded yet. Dynamic events will appear during network congestion.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {events.map((ev, index) => {
              const meta = getEventBadge(ev.event_type);
              const IconComp = meta.icon;
              return (
                <div
                  key={ev.id || index}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '16px',
                    padding: '16px 20px',
                    borderBottom: '1px solid var(--color-hairline)',
                    backgroundColor: index % 2 === 0 ? 'var(--color-surface-1)' : 'var(--color-canvas)',
                  }}
                >
                  {/* Event Type Icon & Badge */}
                  <div style={{ width: '130px', flexShrink: 0 }}>
                    <span
                      className="badge"
                      style={{
                        backgroundColor: meta.bg,
                        color: meta.color,
                        borderColor: meta.color,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '5px',
                        fontSize: '11px',
                        fontWeight: 500,
                      }}
                    >
                      <IconComp size={12} />
                      {meta.label}
                    </span>
                    <div className="caption font-mono" style={{ marginTop: '6px', color: 'var(--color-ink-subtle)' }}>
                      {typeof ev.timestamp === 'number' && ev.timestamp > 1000
                        ? new Date(ev.timestamp * 1000).toLocaleTimeString()
                        : `t = ${ev.timestamp}s`}
                    </div>
                  </div>

                  {/* Message & Context */}
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--color-ink)' }}>
                      {ev.message}
                    </div>
                    {ev.reason && (
                      <div className="caption" style={{ marginTop: '3px', color: 'var(--color-ink-subtle)' }}>
                        Trigger: {ev.reason}
                      </div>
                    )}

                    {/* Before / After Diff Box if available */}
                    {(ev.before_value || ev.after_value) && (
                      <div
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '8px',
                          marginTop: '6px',
                          padding: '3px 8px',
                          borderRadius: 'var(--radius-xs)',
                          backgroundColor: 'var(--color-surface-2)',
                          fontSize: '11px',
                          fontFamily: 'var(--font-mono)',
                          border: '1px solid var(--color-hairline)',
                        }}
                      >
                        <span style={{ color: 'var(--color-ink-subtle)' }}>Before: {ev.before_value}</span>
                        <span style={{ color: 'var(--color-primary)' }}>➔</span>
                        <span style={{ color: 'var(--color-ink)' }}>After: {ev.after_value}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
