import React, { useState } from 'react';
import { useQoSStore } from '../store/useQoSStore';
import { AuditEvent } from '../types';
import { ShieldAlert, Cpu, GitFork, Sliders, CheckCircle, Search, Radio } from 'lucide-react';

export const EventsPage: React.FC = () => {
  const { events } = useQoSStore();
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

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

  const filteredEvents = events.filter((ev: AuditEvent) => {
    const matchesFilter = filterType === 'ALL' || ev.event_type === filterType;
    const term = searchTerm.toLowerCase();
    const matchesSearch =
      !searchTerm ||
      ev.message.toLowerCase().includes(term) ||
      (ev.reason && ev.reason.toLowerCase().includes(term)) ||
      (ev.before_value && ev.before_value.toLowerCase().includes(term)) ||
      (ev.after_value && ev.after_value.toLowerCase().includes(term));
    return matchesFilter && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Header and Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 className="headline">SDN Event Audit Log</h1>
            <span className="badge" style={{ fontSize: '11px', color: 'var(--color-semantic-success)' }}>
              <Radio size={11} className="pulse-dot" style={{ width: '6px', height: '6px' }} />
              Live Auditing
            </span>
          </div>
          <p className="subhead" style={{ fontSize: '15px', marginTop: '4px' }}>
            Real-time chronological timeline of dynamic queue adjustments, meter drops, admission gating, and routing updates
          </p>
        </div>

        {/* Filter and Search Bar */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Filter tabs */}
          <div className="tab-switcher">
            {[
              { id: 'ALL', label: 'All' },
              { id: 'ADAPTATION', label: 'Adaptation' },
              { id: 'METER_DROP', label: 'Meter' },
              { id: 'REROUTE', label: 'Reroute' },
              { id: 'ADMISSION', label: 'Admission' },
            ].map((tab) => (
              <button
                key={tab.id}
                id={`filter-event-${tab.id.toLowerCase()}`}
                onClick={() => setFilterType(tab.id)}
                className={`tab-btn ${filterType === tab.id ? 'tab-btn-selected' : ''}`}
                style={{ fontSize: '12px', padding: '5px 12px' }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search box */}
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '11px', color: 'var(--color-ink-subtle)' }} />
            <input
              type="text"
              placeholder="Search event logs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field"
              style={{ paddingLeft: '32px', width: '200px' }}
            />
          </div>
        </div>
      </div>

      {/* Events List Container */}
      <div className="card-panel" style={{ padding: 0, overflow: 'hidden' }}>
        {filteredEvents.length === 0 ? (
          <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--color-ink-subtle)' }}>
            <Cpu size={24} style={{ margin: '0 auto 8px auto', opacity: 0.5 }} />
            <div style={{ fontWeight: 500, fontSize: '14px', color: 'var(--color-ink)' }}>No Audit Events Found</div>
            <div className="caption" style={{ marginTop: '4px' }}>
              {events.length === 0
                ? 'No events logged yet. Congestion events trigger automatically during the benchmark scenario.'
                : 'No events match the selected filter or search keyword. Try clearing filters.'}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {filteredEvents.map((ev: AuditEvent, index: number) => {
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
