import React, { useState } from 'react';
import { useQoSStore } from '../store/useQoSStore';
import { ClassPolicy, MeterInfo } from '../types';
import { Save, Check, Shield, Zap, AlertCircle, AlertTriangle } from 'lucide-react';

export const PoliciesPage: React.FC = () => {
  const { policies, switchPreset, updatePolicy, savePolicies, toggleQoS, meters } = useQoSStore();
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const activeProfile = policies.profiles[policies.active_profile] || policies.profiles['Balanced'];
  const presets = ['Balanced', 'Voice-First', 'Video-Conference'];

  // Input Validation
  const validationErrors: string[] = [];
  (Object.entries(activeProfile?.classes || {}) as [string, ClassPolicy][]).forEach(([className, classData]) => {
    if (classData.min_rate_kbps > classData.max_rate_kbps) {
      validationErrors.push(`Class '${className}': Min guaranteed rate (${classData.min_rate_kbps} kbps) exceeds max rate (${classData.max_rate_kbps} kbps).`);
    }
    if (classData.target_latency_ms <= 0) {
      validationErrors.push(`Class '${className}': Target latency must be positive.`);
    }
    if (classData.target_jitter_ms <= 0) {
      validationErrors.push(`Class '${className}': Target jitter must be positive.`);
    }
  });

  const isValid = validationErrors.length === 0;

  const handleApply = async () => {
    if (!isValid) return;
    setSaveStatus('saving');
    const success = await savePolicies();
    if (success) {
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2500);
    } else {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="headline">QoS Policy Configuration</h1>
          <p className="subhead" style={{ fontSize: '15px', marginTop: '4px' }}>
            Live profile management, rate guarantees, and SLA target parameters pushed directly to Open vSwitch HTB queues
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            id="btn-policy-master-toggle"
            onClick={toggleQoS}
            className={policies.qos_enabled ? 'btn-primary' : 'btn-secondary'}
          >
            <Shield size={14} />
            {policies.qos_enabled ? 'QoS Master: Active' : 'QoS Master: Bypassed'}
          </button>

          <button
            id="btn-apply-policy"
            onClick={handleApply}
            className="btn-primary"
            disabled={saveStatus === 'saving' || !isValid}
            style={{
              backgroundColor: !isValid
                ? 'var(--color-surface-2)'
                : saveStatus === 'error'
                ? '#e5484d'
                : undefined,
              borderColor: !isValid ? 'var(--color-hairline)' : undefined,
              cursor: !isValid ? 'not-allowed' : 'pointer',
            }}
          >
            {saveStatus === 'saved' ? (
              <Check size={14} />
            ) : saveStatus === 'error' ? (
              <AlertCircle size={14} />
            ) : (
              <Save size={14} />
            )}
            {saveStatus === 'saved'
              ? 'Applied to OVS & Ryu'
              : saveStatus === 'saving'
              ? 'Applying to Queues...'
              : saveStatus === 'error'
              ? 'Apply Failed'
              : !isValid
              ? 'Validation Error'
              : 'Apply Live Policy'}
          </button>
        </div>
      </div>

      {/* Validation Errors Box */}
      {!isValid && (
        <div
          style={{
            backgroundColor: 'rgba(229, 72, 77, 0.1)',
            border: '1px solid rgba(229, 72, 77, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            fontSize: '13px',
            color: '#e5484d',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600, marginBottom: '4px' }}>
            <AlertTriangle size={14} />
            Policy Form Validation Issues:
          </div>
          <ul style={{ paddingLeft: '20px', lineHeight: 1.5 }}>
            {validationErrors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Preset Profiles Selector (DESIGN.md pricing-tab spec) */}
      <div className="card-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px' }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: '15px', color: 'var(--color-ink)' }}>Preset Profiles</div>
          <div className="caption" style={{ marginTop: '2px' }}>
            {activeProfile?.description}
          </div>
        </div>

        <div className="tab-switcher">
          {presets.map((p) => (
            <button
              key={p}
              id={`preset-${p.toLowerCase()}`}
              onClick={() => switchPreset(p)}
              className={`tab-btn ${policies.active_profile === p ? 'tab-btn-selected' : ''}`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Per-Class Policy Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-md)' }}>
        {Object.entries(activeProfile?.classes || {}).map(([className, classData]) => {
          const isVoice = className === 'voice';
          const isVideo = className === 'video';

          return (
            <div key={className} className="card-panel">
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <span
                  className={`badge ${isVoice ? 'badge-voice' : isVideo ? 'badge-video' : 'badge-bulk'}`}
                  style={{ textTransform: 'uppercase', fontSize: '12px', fontWeight: 600 }}
                >
                  Class: {className}
                </span>
                <span className="caption" style={{ color: 'var(--color-ink-subtle)' }}>
                  Queue #{classData.queue_id} (DSCP {classData.dscp})
                </span>
              </div>

              {/* Form Inputs Grid */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--color-ink-muted)' }}>Min Guaranteed Rate:</span>
                    <span className="font-mono" style={{ color: 'var(--color-ink)' }}>{classData.min_rate_kbps} kbps</span>
                  </div>
                  <input
                    type="range"
                    min="100"
                    max="5000"
                    step="100"
                    value={classData.min_rate_kbps}
                    onChange={(e) => updatePolicy(policies.active_profile, className, 'min_rate_kbps', Number(e.target.value))}
                    style={{ width: '100%', accentColor: 'var(--color-primary)' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                    <span style={{ color: 'var(--color-ink-muted)' }}>Max Ceiling Rate:</span>
                    <span className="font-mono" style={{ color: 'var(--color-ink)' }}>{classData.max_rate_kbps} kbps</span>
                  </div>
                  <input
                    type="range"
                    min="500"
                    max="10000"
                    step="200"
                    value={classData.max_rate_kbps}
                    onChange={(e) => updatePolicy(policies.active_profile, className, 'max_rate_kbps', Number(e.target.value))}
                    style={{ width: '100%', accentColor: 'var(--color-primary)' }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '4px' }}>
                  <div>
                    <label style={{ fontSize: '11px', color: 'var(--color-ink-subtle)', textTransform: 'uppercase' }}>Target Latency</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                      <input
                        type="number"
                        className="input-field"
                        style={{ width: '100%', padding: '4px 8px', fontSize: '13px' }}
                        value={classData.target_latency_ms}
                        onChange={(e) => updatePolicy(policies.active_profile, className, 'target_latency_ms', Number(e.target.value))}
                      />
                      <span className="caption">ms</span>
                    </div>
                  </div>

                  <div>
                    <label style={{ fontSize: '11px', color: 'var(--color-ink-subtle)', textTransform: 'uppercase' }}>Target Jitter</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                      <input
                        type="number"
                        className="input-field"
                        style={{ width: '100%', padding: '4px 8px', fontSize: '13px' }}
                        value={classData.target_jitter_ms}
                        onChange={(e) => updatePolicy(policies.active_profile, className, 'target_jitter_ms', Number(e.target.value))}
                      />
                      <span className="caption">ms</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Dynamic Bandwidth Allocation Thresholds Box */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Zap size={16} color="var(--color-primary)" />
          <div className="card-title">Dynamic Allocation & Hysteresis Thresholds</div>
        </div>
        <p className="caption" style={{ marginBottom: '16px' }}>
          When bottleneck link utilization crosses the High Watermark (80%), bulk queues are automatically clamped.
          The controller releases allocations only after utilization drops below the Low Watermark (60%) with a 4s cooldown to eliminate flapping.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-2)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-hairline)' }}>
            <div className="caption">HIGH WATERMARK</div>
            <div className="headline" style={{ fontSize: '22px', marginTop: '4px', color: '#e5484d' }}>
              {(policies.dynamic_allocation.high_watermark_utilization * 100).toFixed(0)}%
            </div>
            <div className="caption" style={{ marginTop: '2px' }}>Triggers rate reduction</div>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-2)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-hairline)' }}>
            <div className="caption">LOW WATERMARK</div>
            <div className="headline" style={{ fontSize: '22px', marginTop: '4px', color: 'var(--color-semantic-success)' }}>
              {(policies.dynamic_allocation.low_watermark_utilization * 100).toFixed(0)}%
            </div>
            <div className="caption" style={{ marginTop: '2px' }}>Triggers rate recovery</div>
          </div>

          <div style={{ padding: '12px', backgroundColor: 'var(--color-surface-2)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-hairline)' }}>
            <div className="caption">HYSTERESIS COOLDOWN</div>
            <div className="headline" style={{ fontSize: '22px', marginTop: '4px', color: 'var(--color-ink)' }}>
              {policies.dynamic_allocation.cooldown_seconds}s
            </div>
            <div className="caption" style={{ marginTop: '2px' }}>Oscillation suppression</div>
          </div>
        </div>
      </div>

      {/* OpenFlow 1.3 Meter Management & Hit Counters */}
      <div className="card-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div>
            <div className="card-title">OpenFlow 1.3 Meters & Rate-Limiting Bands</div>
            <p className="caption" style={{ marginTop: '2px' }}>
              Hardware/OVS rate limiting applied on packet ingress to enforce flow bounds and police rogue UDP flooders
            </p>
          </div>
          <span className="badge" style={{ backgroundColor: 'rgba(94, 106, 210, 0.12)', color: 'var(--color-primary)' }}>
            OF 1.3 OFPInstructionMeter
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {meters.map((meter) => {
            const isDrop = meter.action === 'drop';
            return (
              <div
                key={meter.id}
                style={{
                  padding: '16px',
                  backgroundColor: 'var(--color-surface-2)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-hairline)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--color-ink)' }}>
                    Meter #{meter.id}: {meter.name}
                  </div>
                  <span
                    className="badge"
                    style={{
                      backgroundColor: isDrop ? 'rgba(229, 72, 77, 0.12)' : 'rgba(247, 107, 21, 0.12)',
                      color: isDrop ? '#e5484d' : '#f76b15',
                      fontSize: '11px',
                    }}
                  >
                    Action: {meter.action.toUpperCase()}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px', marginBottom: '12px' }}>
                  <div>
                    <span style={{ color: 'var(--color-ink-subtle)' }}>Rate Limit: </span>
                    <span className="font-mono" style={{ color: 'var(--color-ink)', fontWeight: 500 }}>
                      {meter.rate_kbps} kbps
                    </span>
                  </div>
                  <div>
                    <span style={{ color: 'var(--color-ink-subtle)' }}>Burst Allowance: </span>
                    <span className="font-mono" style={{ color: 'var(--color-ink)', fontWeight: 500 }}>
                      {meter.burst_kbps} kbps
                    </span>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--color-hairline)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                  <div>
                    <div className="caption">PACKETS PROCESSED</div>
                    <div className="font-mono" style={{ color: 'var(--color-ink)', marginTop: '2px' }}>
                      {meter.packet_in_count.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="caption">{isDrop ? 'PACKETS DROPPED' : 'PACKETS REMARKED'}</div>
                    <div className="font-mono" style={{ color: isDrop ? '#e5484d' : '#f76b15', marginTop: '2px', fontWeight: 600 }}>
                      {meter.drop_packet_count.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div className="caption">BYTES ENFORCED</div>
                    <div className="font-mono" style={{ color: 'var(--color-ink-muted)', marginTop: '2px' }}>
                      {(meter.drop_byte_count / 1024 / 1024).toFixed(1)} MB
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
