import React, { useState } from 'react';
import { useQoSStore } from '../store/useQoSStore';
import { Search, ShieldCheck, ArrowRight } from 'lucide-react';

export const FlowsPage: React.FC = () => {
  const { flows } = useQoSStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClass, setSelectedClass] = useState<string>('all');

  const filteredFlows = flows.filter((f) => {
    const matchesSearch =
      f.src_ip.includes(searchTerm) ||
      f.dst_ip.includes(searchTerm) ||
      f.protocol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesClass = selectedClass === 'all' || f.class_name === selectedClass;
    return matchesSearch && matchesClass;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Header and Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="headline">Active Network Flows</h1>
          <p className="subhead" style={{ fontSize: '15px', marginTop: '4px' }}>
            5-tuple classification, OpenFlow 1.3 queue assignments, and live admission control status
          </p>
        </div>

        {/* Search & Filter */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {/* Class Filters (DESIGN.md tab-switcher) */}
          <div className="tab-switcher">
            {['all', 'voice', 'video', 'bulk'].map((c) => (
              <button
                key={c}
                onClick={() => setSelectedClass(c)}
                className={`tab-btn ${selectedClass === c ? 'tab-btn-selected' : ''}`}
                style={{ textTransform: 'capitalize' }}
              >
                {c}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '11px', color: 'var(--color-ink-subtle)' }} />
            <input
              type="text"
              placeholder="Search IP, port, ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field"
              style={{ paddingLeft: '32px', width: '220px' }}
            />
          </div>
        </div>
      </div>

      {/* Flows Table Panel */}
      <div className="card-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Flow ID</th>
              <th>5-Tuple & Protocol</th>
              <th>Class</th>
              <th>HTB Queue</th>
              <th>Forwarding Path</th>
              <th>Rate (kbps)</th>
              <th>Packets</th>
              <th>Admission Decision</th>
            </tr>
          </thead>
          <tbody>
            {filteredFlows.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '32px', color: 'var(--color-ink-subtle)' }}>
                  No active flows match the current filter.
                </td>
              </tr>
            ) : (
              filteredFlows.map((flow) => {
                const isVoice = flow.class_name === 'voice';
                const isVideo = flow.class_name === 'video';
                return (
                  <tr key={flow.id}>
                    <td className="font-mono" style={{ color: 'var(--color-ink)', fontWeight: 500 }}>
                      {flow.id}
                    </td>
                    <td>
                      <div className="font-mono" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span className="badge" style={{ fontSize: '10px', padding: '1px 5px' }}>{flow.protocol}</span>
                        <span>{flow.src_ip}:{flow.src_port}</span>
                        <ArrowRight size={12} style={{ color: 'var(--color-ink-subtle)' }} />
                        <span>{flow.dst_ip}:{flow.dst_port}</span>
                      </div>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          isVoice ? 'badge-voice' : isVideo ? 'badge-video' : 'badge-bulk'
                        }`}
                        style={{ textTransform: 'capitalize' }}
                      >
                        {flow.class_name}
                      </span>
                    </td>
                    <td>
                      <span className="font-mono" style={{ color: 'var(--color-ink)' }}>
                        Queue #{flow.queue_id}
                      </span>
                    </td>
                    <td className="font-mono" style={{ color: flow.path.includes('s3') ? 'var(--color-primary)' : 'var(--color-ink-muted)' }}>
                      {flow.path}
                    </td>
                    <td className="font-mono" style={{ color: 'var(--color-ink)' }}>
                      {flow.rate_kbps.toFixed(1)}
                    </td>
                    <td className="font-mono" style={{ color: 'var(--color-ink-subtle)' }}>
                      {flow.packets_count.toLocaleString()}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor:
                            flow.decision === 'admit'
                              ? 'rgba(39, 166, 68, 0.15)'
                              : flow.decision === 'downgrade'
                              ? 'rgba(247, 107, 21, 0.15)'
                              : 'rgba(229, 72, 77, 0.15)',
                          color:
                            flow.decision === 'admit'
                              ? 'var(--color-semantic-success)'
                              : flow.decision === 'downgrade'
                              ? '#f76b15'
                              : '#e5484d',
                          borderColor:
                            flow.decision === 'admit'
                              ? 'rgba(39, 166, 68, 0.3)'
                              : 'rgba(229, 72, 77, 0.3)',
                          textTransform: 'uppercase',
                          fontWeight: 500,
                          fontSize: '11px',
                        }}
                      >
                        <ShieldCheck size={11} style={{ marginRight: '4px' }} />
                        {flow.decision}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
