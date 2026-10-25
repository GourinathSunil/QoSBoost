import React from 'react';
import { useQoSStore } from '../store/useQoSStore';
import { ReactFlowTopology } from '../components/ReactFlowTopology';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, LineChart, Line, ReferenceLine } from 'recharts';
import { Activity, Zap, CheckCircle2, AlertTriangle } from 'lucide-react';

export const OverviewPage: React.FC = () => {
  const { telemetry, history, policies, connected, useMock, setUseMock } = useQoSStore();

  const activeProfile = policies.profiles[policies.active_profile] || policies.profiles['Balanced'];
  const voiceTargetLatency = activeProfile?.classes?.voice?.target_latency_ms || 30.0;
  const voiceTargetJitter = activeProfile?.classes?.voice?.target_jitter_ms || 10.0;

  const voiceLatency = telemetry.voice.latency_ms;
  const voiceJitter = telemetry.voice.jitter_ms;
  const voiceLoss = telemetry.voice.loss_percent;
  const linkUtil = telemetry.link_utilization;

  const isLatencyViolated = voiceLatency > voiceTargetLatency;
  const isJitterViolated = voiceJitter > voiceTargetJitter;
  const isLossViolated = voiceLoss > 0.5;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Offline Alert Banner */}
      {!connected && !useMock && (
        <div
          style={{
            backgroundColor: 'rgba(247, 107, 21, 0.1)',
            border: '1px solid rgba(247, 107, 21, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '13px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f76b15' }}>
            <AlertTriangle size={16} />
            <span>OpenFlow controller is offline. Enable <strong>Mock Demo Mode</strong> for full synthetic interactive telemetry.</span>
          </div>
          <button
            onClick={() => setUseMock(true)}
            className="btn-primary"
            style={{ fontSize: '12px', padding: '4px 10px', height: 'auto' }}
          >
            Enable Mock Demo
          </button>
        </div>
      )}

      {/* KPI Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-md)' }}>
        {/* Card 1: Voice Latency */}
        <div className="card-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="caption" style={{ textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              Voice One-Way Latency
            </span>
            <Activity size={16} color={isLatencyViolated ? '#e5484d' : 'var(--color-primary)'} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
            <span className="display-md" style={{ color: isLatencyViolated ? '#e5484d' : 'var(--color-ink)' }}>
              {voiceLatency.toFixed(1)}
            </span>
            <span className="caption" style={{ color: 'var(--color-ink-subtle)' }}>ms</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px' }}>
            {isLatencyViolated ? (
              <span style={{ color: '#e5484d', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <AlertTriangle size={12} /> Target SLA ({voiceTargetLatency}ms) Exceeded
              </span>
            ) : (
              <span style={{ color: 'var(--color-semantic-success)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <CheckCircle2 size={12} /> Within SLA Target (&lt;{voiceTargetLatency}ms)
              </span>
            )}
          </div>
        </div>

        {/* Card 2: Voice Jitter */}
        <div className="card-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="caption" style={{ textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              Voice RFC 3550 Jitter
            </span>
            <Zap size={16} color={isJitterViolated ? '#e5484d' : 'var(--color-primary)'} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
            <span className="display-md" style={{ color: isJitterViolated ? '#e5484d' : 'var(--color-ink)' }}>
              {voiceJitter.toFixed(1)}
            </span>
            <span className="caption" style={{ color: 'var(--color-ink-subtle)' }}>ms</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px' }}>
            <span style={{ color: isJitterViolated ? '#e5484d' : 'var(--color-semantic-success)' }}>
              Target SLA: &lt;{voiceTargetJitter}ms (Queue 1 Priority)
            </span>
          </div>
        </div>

        {/* Card 3: Packet Loss */}
        <div className="card-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="caption" style={{ textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              Voice Packet Loss
            </span>
            <span className="badge" style={{ fontSize: '11px' }}>EF DSCP 46</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
            <span className="display-md" style={{ color: isLossViolated ? '#e5484d' : 'var(--color-ink)' }}>
              {voiceLoss.toFixed(1)}%
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px' }}>
            <span style={{ color: isLossViolated ? '#e5484d' : 'var(--color-semantic-success)' }}>
              {voiceLoss === 0.0 ? '0.0% Loss (Strict Isolation)' : `${voiceLoss}% Drops in FIFO buffer`}
            </span>
          </div>
        </div>

        {/* Card 4: Bottleneck Link Utilization */}
        <div className="card-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="caption" style={{ textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              Bottleneck Saturation
            </span>
            <span className="badge" style={{ fontSize: '11px' }}>10 Mbps Link</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
            <span className="display-md" style={{ color: linkUtil > 80 ? '#e5484d' : 'var(--color-ink)' }}>
              {linkUtil.toFixed(1)}%
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px' }}>
            <span style={{ color: linkUtil > 80 ? '#e5484d' : 'var(--color-ink-subtle)' }}>
              {linkUtil > 80 ? 'Congested: Dynamic Allocator Engaged' : 'Nominal Headroom Available'}
            </span>
          </div>
        </div>

        {/* Card 5: Active Flows */}
        <div className="card-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="caption" style={{ textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              Active Network Flows
            </span>
            <span className="badge" style={{ fontSize: '11px' }}>5-Tuple Cached</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
            <span className="display-md" style={{ color: 'var(--color-ink)' }}>
              {telemetry.active_flows_count}
            </span>
            <span className="caption" style={{ color: 'var(--color-ink-subtle)' }}>flows</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px', fontSize: '12px' }}>
            <span style={{ color: 'var(--color-ink-muted)' }}>
              1 VoIP (Q1) • 1 Video (Q2) • 2 Bulk (Q3)
            </span>
          </div>
        </div>
      </div>

      {/* Topology Canvas (React Flow) */}
      <ReactFlowTopology />

      {/* Telemetry Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: 'var(--space-lg)' }}>
        {/* Chart 1: Bandwidth Breakdown by Class */}
        <div className="card-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <div className="card-title">Per-Class Bandwidth Distribution</div>
              <div className="caption" style={{ marginTop: '2px' }}>
                Real-time throughput stacked by OpenFlow traffic class (kbps)
              </div>
            </div>
            <div style={{ display: 'flex', gap: '12px', fontSize: '11px' }}>
              <span style={{ color: 'var(--color-primary)' }}>• Voice (Queue 1)</span>
              <span style={{ color: 'var(--color-brand-secure)' }}>• Video (Queue 2)</span>
              <span style={{ color: 'var(--color-ink-muted)' }}>• Bulk (Queue 3)</span>
            </div>
          </div>

          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="timestamp" tick={false} stroke="var(--color-hairline)" />
                <YAxis stroke="var(--color-hairline)" tick={{ fill: 'var(--color-ink-subtle)', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--color-surface-2)',
                    borderColor: 'var(--color-hairline-strong)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '12px',
                  }}
                />
                <Area type="monotone" dataKey="voice.throughput_kbps" stackId="1" stroke="var(--color-primary)" fill="var(--color-primary)" fillOpacity={0.6} name="Voice (kbps)" />
                <Area type="monotone" dataKey="video.throughput_kbps" stackId="1" stroke="var(--color-brand-secure)" fill="var(--color-brand-secure)" fillOpacity={0.4} name="Video (kbps)" />
                <Area type="monotone" dataKey="bulk.throughput_kbps" stackId="1" stroke="#3e3e44" fill="#23252a" fillOpacity={0.8} name="Bulk (kbps)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Real-Time Latency & Jitter with Target Threshold */}
        <div className="card-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <div className="card-title">Latency & Jitter vs Policy Target</div>
              <div className="caption" style={{ marginTop: '2px' }}>
                Voice latency history with policy target ceiling ({voiceTargetLatency}ms)
              </div>
            </div>
            <span className="badge badge-voice">Target: {voiceTargetLatency}ms</span>
          </div>

          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="timestamp" tick={false} stroke="var(--color-hairline)" />
                <YAxis stroke="var(--color-hairline)" domain={[0, 200]} tick={{ fill: 'var(--color-ink-subtle)', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--color-surface-2)',
                    borderColor: 'var(--color-hairline-strong)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '12px',
                  }}
                />
                <ReferenceLine y={voiceTargetLatency} stroke="#e5484d" strokeDasharray="3 3" label={{ value: `SLA Latency (${voiceTargetLatency}ms)`, fill: '#e5484d', fontSize: 10, position: 'insideTopRight' }} />
                <ReferenceLine y={voiceTargetJitter} stroke="#828fff" strokeDasharray="2 2" label={{ value: `Target Jitter (${voiceTargetJitter}ms)`, fill: '#828fff', fontSize: 10, position: 'insideBottomRight' }} />
                <Line type="monotone" dataKey="voice.latency_ms" stroke="var(--color-primary)" strokeWidth={2} dot={false} name="Voice Latency (ms)" />
                <Line type="monotone" dataKey="voice.jitter_ms" stroke="#828fff" strokeWidth={1.5} dot={false} strokeDasharray="2 2" name="Jitter (ms)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
