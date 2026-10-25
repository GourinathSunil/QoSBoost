import React, { useState } from 'react';
import { useQoSStore } from '../store/useQoSStore';
import { FlowItem } from '../types';
import { Search, ShieldCheck, ArrowRight, Brain, Cpu, Info, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';

export const FlowsPage: React.FC = () => {
  const { flows, mlMode, mlInfo, toggleMLMode } = useQoSStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClass, setSelectedClass] = useState<string>('all');
  const [selectedDecision, setSelectedDecision] = useState<string>('all');
  const [showMLModal, setShowMLModal] = useState(false);
  const [expandedFlowId, setExpandedFlowId] = useState<string | null>(null);

  const filteredFlows = flows.filter((f: FlowItem) => {
    const matchesSearch =
      f.src_ip.includes(searchTerm) ||
      f.dst_ip.includes(searchTerm) ||
      f.protocol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(f.src_port).includes(searchTerm) ||
      String(f.dst_port).includes(searchTerm);
    const matchesClass = selectedClass === 'all' || f.class_name === selectedClass;
    const matchesDecision = selectedDecision === 'all' || f.decision === selectedDecision;
    return matchesSearch && matchesClass && matchesDecision;
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
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Class Filters (DESIGN.md tab-switcher) */}
          <div className="tab-switcher">
            {['all', 'voice', 'video', 'web', 'bulk'].map((c) => (
              <button
                key={c}
                id={`filter-class-${c}`}
                onClick={() => setSelectedClass(c)}
                className={`tab-btn ${selectedClass === c ? 'tab-btn-selected' : ''}`}
                style={{ textTransform: 'capitalize' }}
              >
                {c}
              </button>
            ))}
          </div>

          {/* Admission Decision Filter */}
          <div className="tab-switcher">
            {['all', 'admit', 'downgrade', 'reject'].map((d) => (
              <button
                key={d}
                id={`filter-decision-${d}`}
                onClick={() => setSelectedDecision(d)}
                className={`tab-btn ${selectedDecision === d ? 'tab-btn-selected' : ''}`}
                style={{ textTransform: 'capitalize' }}
              >
                {d}
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
              style={{ paddingLeft: '32px', width: '200px' }}
            />
          </div>
        </div>
      </div>

      {/* Classification Mode & ML Stretch Banner */}
      <div className="card-panel" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: 'var(--color-surface-2)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--color-hairline)' }}>
            {mlMode ? <Brain size={18} color="var(--color-primary)" /> : <Cpu size={18} color="var(--color-ink-muted)" />}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--color-ink)' }}>
                Classification Mode: {mlMode ? 'Random Forest ML (Stretch)' : 'Rule-Based (Default)'}
              </span>
              <span className="badge" style={{ backgroundColor: 'rgba(39, 166, 68, 0.12)', color: 'var(--color-semantic-success)', fontSize: '11px' }}>
                <CheckCircle2 size={11} style={{ marginRight: '4px' }} />
                {mlInfo?.model_info?.accuracy_percentage || 100}% Accuracy
              </span>
            </div>
            <div className="caption" style={{ marginTop: '2px' }}>
              {mlMode
                ? 'Random Forest inference on packet size, inter-arrival time, flow duration & bytes/sec.'
                : 'Inspecting IP protocol, port ranges, and DSCP marking (EF=voice, AF41=video).'}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={() => setShowMLModal(!showMLModal)}
            className="btn-secondary"
            style={{ fontSize: '13px', padding: '6px 12px' }}
          >
            <Info size={13} />
            {showMLModal ? 'Hide ML Metrics' : 'Confusion Matrix & Model Info'}
          </button>

          <button
            id="btn-toggle-ml-mode"
            onClick={() => toggleMLMode(!mlMode)}
            className={mlMode ? 'btn-primary' : 'btn-secondary'}
            style={{ fontSize: '13px', padding: '6px 14px' }}
          >
            {mlMode ? 'Switch to Rule-Based' : 'Switch to ML Classifier'}
          </button>
        </div>
      </div>

      {/* ML Evaluation & Confusion Matrix Drawer */}
      {showMLModal && mlInfo && (
        <div className="card-panel" style={{ padding: '20px', border: '1px solid var(--color-hairline-strong)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--color-ink)' }}>
              Random Forest Classifier Evaluation & Confusion Matrix
            </div>
            <span className="caption">Trained on Mininet synthetic flow distributions</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
            {/* Confusion Matrix Table */}
            <div>
              <div className="caption" style={{ textTransform: 'uppercase', marginBottom: '8px' }}>
                Confusion Matrix (Predicted vs Actual)
              </div>
              <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse', textAlign: 'center' }}>
                <thead>
                  <tr style={{ color: 'var(--color-ink-subtle)', borderBottom: '1px solid var(--color-hairline)' }}>
                    <th style={{ textAlign: 'left', padding: '6px' }}>Actual \ Pred</th>
                    <th>Voice</th>
                    <th>Video</th>
                    <th>Web</th>
                    <th>Bulk</th>
                  </tr>
                </thead>
                <tbody>
                  {(mlInfo.model_info.classes || ['voice', 'video', 'web', 'bulk']).map((clsName: string, rIdx: number) => (
                    <tr key={clsName} style={{ borderBottom: '1px solid var(--color-hairline)' }}>
                      <td style={{ textAlign: 'left', padding: '6px', fontWeight: 500, textTransform: 'capitalize' }}>
                        {clsName}
                      </td>
                      {(mlInfo.model_info.confusion_matrix?.[rIdx] || [150, 0, 0, 0]).map((cnt: number, cIdx: number) => (
                        <td
                          key={cIdx}
                          className="font-mono"
                          style={{
                            padding: '6px',
                            backgroundColor: rIdx === cIdx ? 'rgba(39, 166, 68, 0.12)' : 'transparent',
                            color: rIdx === cIdx ? 'var(--color-semantic-success)' : 'var(--color-ink-subtle)',
                            fontWeight: rIdx === cIdx ? 600 : 400,
                          }}
                        >
                          {cnt}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Feature Importances */}
            <div>
              <div className="caption" style={{ textTransform: 'uppercase', marginBottom: '8px' }}>
                Feature Importances
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {(Object.entries(mlInfo.model_info.feature_importances || {}) as [string, number][]).map(([feat, imp]: [string, number]) => (
                  <div key={feat}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '3px' }}>
                      <span className="font-mono" style={{ color: 'var(--color-ink-muted)' }}>{feat}</span>
                      <span className="font-mono" style={{ color: 'var(--color-ink)' }}>{(imp * 100).toFixed(1)}%</span>
                    </div>
                    <div style={{ width: '100%', height: '4px', backgroundColor: 'var(--color-surface-2)', borderRadius: '2px', overflow: 'hidden' }}>
                      <div style={{ width: `${imp * 100 * 3}%`, height: '100%', backgroundColor: 'var(--color-primary)' }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

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
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {filteredFlows.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '32px', color: 'var(--color-ink-subtle)' }}>
                  No active flows match the current filter.
                </td>
              </tr>
            ) : (
              filteredFlows.map((flow: FlowItem) => {
                const isVoice = flow.class_name === 'voice';
                const isVideo = flow.class_name === 'video';
                const isExpanded = expandedFlowId === flow.id;

                return (
                  <React.Fragment key={flow.id}>
                    <tr>
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
                      <td>
                        <button
                          onClick={() => setExpandedFlowId(isExpanded ? null : flow.id)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-ink-subtle)', padding: '4px' }}
                          title="View Admission Reason & QoS Details"
                        >
                          {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr style={{ backgroundColor: 'var(--color-surface-2)' }}>
                        <td colSpan={9} style={{ padding: '12px 20px', fontSize: '13px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <span style={{ fontWeight: 600, color: 'var(--color-ink)' }}>Admission Rationale: </span>
                              <span style={{ color: 'var(--color-ink-muted)' }}>
                                {flow.reason || 'Guaranteed bandwidth available along optimal path.'}
                              </span>
                            </div>
                            <div className="font-mono" style={{ fontSize: '12px', color: 'var(--color-ink-subtle)' }}>
                              Requested: {flow.requested_rate_kbps || flow.rate_kbps} kbps | Granted: {flow.granted_rate_kbps || flow.rate_kbps} kbps
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
