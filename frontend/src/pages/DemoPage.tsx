import React, { useEffect } from 'react';
import { useQoSStore } from '../store/useQoSStore';
import { Play, Square, Download, ArrowRight } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

export const DemoPage: React.FC = () => {
  const { scenarioRunning, scenarioElapsed, startScenario, stopScenario, report, fetchReport } = useQoSStore();

  useEffect(() => {
    // If report is not loaded, fetch initial report
    if (!report) {
      fetchReport();
    }
  }, [report, fetchReport]);

  const handleStart = async (qosOn: boolean) => {
    await startScenario(qosOn);
  };

  const handleExportJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `qosboost-evaluation-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Phase tracker logic
  const getPhaseInfo = (t: number) => {
    if (t < 15) return { stage: 1, label: 'Stage 1: Real-Time Flow Initialization (t=0..15s)', desc: '1 VoIP call (100 kbps) + 1 HD Video stream (3.2 Mbps) active.' };
    if (t < 40) return { stage: 2, label: 'Stage 2: Bulk Congestion (t=15..40s)', desc: '2 TCP bulk flows saturate the 10 Mbps bottleneck link.' };
    if (t < 60) return { stage: 3, label: 'Stage 3: Extreme Overload & Rogue Flooder (t=40..60s)', desc: '3rd bulk host + rogue UDP flooder start; OF1.3 meter and rerouting trigger.' };
    return { stage: 4, label: 'Stage 4: Traffic Normalization (t=60s+)', desc: 'Bulk traffic terminates; network stabilizes.' };
  };

  const currentPhase = getPhaseInfo(scenarioElapsed);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
      {/* Header and Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="headline">Demo Mode & Evaluation Runner</h1>
          <p className="subhead" style={{ fontSize: '15px', marginTop: '4px' }}>
            Automated 60-90 second scripted before/after scenario demonstrating traffic isolation under severe link saturation
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {!scenarioRunning ? (
            <>
              <button
                id="btn-run-qos-on"
                onClick={() => handleStart(true)}
                className="btn-primary"
              >
                <Play size={14} />
                Run Scenario (QoS ON)
              </button>

              <button
                id="btn-run-qos-off"
                onClick={() => handleStart(false)}
                className="btn-secondary"
              >
                <Play size={14} />
                Run Scenario (QoS OFF)
              </button>
            </>
          ) : (
            <button
              id="btn-stop-scenario"
              onClick={stopScenario}
              className="btn-secondary"
              style={{ borderColor: '#e5484d', color: '#e5484d' }}
            >
              <Square size={14} />
              Stop Active Scenario ({scenarioElapsed}s)
            </button>
          )}

          <button
            id="btn-export-report"
            onClick={handleExportJSON}
            className="btn-secondary"
            disabled={!report}
          >
            <Download size={14} />
            Export Report (JSON)
          </button>
        </div>
      </div>

      {/* Scripted Timeline Progress Tracker */}
      <div className="card-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div>
            <span className="caption" style={{ textTransform: 'uppercase', letterSpacing: '0.4px' }}>
              Scripted Timeline Status
            </span>
            <div style={{ fontWeight: 600, fontSize: '15px', color: 'var(--color-ink)', marginTop: '2px' }}>
              {currentPhase.label}
            </div>
            <div className="caption" style={{ marginTop: '2px' }}>{currentPhase.desc}</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span className="font-mono" style={{ fontSize: '20px', fontWeight: 600, color: 'var(--color-primary)' }}>
              {scenarioRunning ? `${scenarioElapsed}s / 65s` : 'Ready'}
            </span>
          </div>
        </div>

        {/* Progress bar container */}
        <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--color-surface-2)', borderRadius: '3px', overflow: 'hidden' }}>
          <div
            style={{
              width: `${Math.min(100, (scenarioElapsed / 65) * 100)}%`,
              height: '100%',
              backgroundColor: 'var(--color-primary)',
              transition: 'width 0.3s ease',
            }}
          />
        </div>

        {/* Timeline milestone marks */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '11px', color: 'var(--color-ink-subtle)' }}>
          <span>t=0: Real-time start</span>
          <span>t=15s: Bulk congestion</span>
          <span>t=40s: Flooder + Reroute</span>
          <span>t=60s: Bulk stop</span>
          <span>t=65s: Complete</span>
        </div>
      </div>

      {/* Side-by-Side Comparison KPI Matrix */}
      {report && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-md)' }}>
          {/* Box 1: Voice Latency Comparison */}
          <div className="card-panel">
            <div className="caption" style={{ textTransform: 'uppercase' }}>Latency Improvement</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
              <span className="display-md" style={{ color: 'var(--color-semantic-success)' }}>
                {report.improvement_percentages.latency_reduction_percent}%
              </span>
              <span style={{ fontSize: '14px', color: 'var(--color-semantic-success)', fontWeight: 500 }}>
                Reduction
              </span>
            </div>
            <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', fontSize: '13px', borderTop: '1px solid var(--color-hairline)', paddingTop: '10px' }}>
              <div>
                <span style={{ color: 'var(--color-ink-subtle)' }}>QoS OFF: </span>
                <span className="font-mono" style={{ color: '#e5484d' }}>{report.baseline_off.avg_voice_latency_ms} ms</span>
              </div>
              <ArrowRight size={14} style={{ color: 'var(--color-ink-subtle)' }} />
              <div>
                <span style={{ color: 'var(--color-ink-subtle)' }}>QoS ON: </span>
                <span className="font-mono" style={{ color: 'var(--color-semantic-success)', fontWeight: 600 }}>{report.qos_on.avg_voice_latency_ms} ms</span>
              </div>
            </div>
          </div>

          {/* Box 2: Voice Jitter Comparison */}
          <div className="card-panel">
            <div className="caption" style={{ textTransform: 'uppercase' }}>Jitter Improvement</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
              <span className="display-md" style={{ color: 'var(--color-semantic-success)' }}>
                {report.improvement_percentages.jitter_reduction_percent}%
              </span>
              <span style={{ fontSize: '14px', color: 'var(--color-semantic-success)', fontWeight: 500 }}>
                Reduction
              </span>
            </div>
            <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', fontSize: '13px', borderTop: '1px solid var(--color-hairline)', paddingTop: '10px' }}>
              <div>
                <span style={{ color: 'var(--color-ink-subtle)' }}>QoS OFF: </span>
                <span className="font-mono" style={{ color: '#e5484d' }}>{report.baseline_off.avg_voice_jitter_ms} ms</span>
              </div>
              <ArrowRight size={14} style={{ color: 'var(--color-ink-subtle)' }} />
              <div>
                <span style={{ color: 'var(--color-ink-subtle)' }}>QoS ON: </span>
                <span className="font-mono" style={{ color: 'var(--color-semantic-success)', fontWeight: 600 }}>{report.qos_on.avg_voice_jitter_ms} ms</span>
              </div>
            </div>
          </div>

          {/* Box 3: Packet Loss Comparison */}
          <div className="card-panel">
            <div className="caption" style={{ textTransform: 'uppercase' }}>Packet Loss Elimination</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '8px' }}>
              <span className="display-md" style={{ color: 'var(--color-semantic-success)' }}>
                {report.improvement_percentages.loss_elimination_percent}%
              </span>
              <span style={{ fontSize: '14px', color: 'var(--color-semantic-success)', fontWeight: 500 }}>
                Elimination
              </span>
            </div>
            <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', fontSize: '13px', borderTop: '1px solid var(--color-hairline)', paddingTop: '10px' }}>
              <div>
                <span style={{ color: 'var(--color-ink-subtle)' }}>QoS OFF: </span>
                <span className="font-mono" style={{ color: '#e5484d' }}>{report.baseline_off.avg_voice_loss_percent}%</span>
              </div>
              <ArrowRight size={14} style={{ color: 'var(--color-ink-subtle)' }} />
              <div>
                <span style={{ color: 'var(--color-ink-subtle)' }}>QoS ON: </span>
                <span className="font-mono" style={{ color: 'var(--color-semantic-success)', fontWeight: 600 }}>{report.qos_on.avg_voice_loss_percent}%</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Side-by-Side Comparison Trajectory Chart */}
      {report && (
        <div className="card-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <div className="card-title">Comparative Latency Overlay: QoS OFF vs QoS ON</div>
              <div className="caption" style={{ marginTop: '2px' }}>
                60-second time-series comparison showing voice latency spikes under unmanaged FIFO vs guaranteed OpenFlow HTB queue
              </div>
            </div>
            <div style={{ display: 'flex', gap: '16px', fontSize: '12px' }}>
              <span style={{ color: '#e5484d' }}>● QoS OFF (FIFO Drop-tail)</span>
              <span style={{ color: 'var(--color-primary)' }}>● QoS ON (HTB Priority)</span>
            </div>
          </div>

          <div style={{ width: '100%', height: '280px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={report.baseline_trajectory.map((basePoint, idx) => ({
                  time: basePoint.timestamp,
                  qos_off_lat: basePoint.voice.latency_ms,
                  qos_on_lat: report.qos_on_trajectory[idx]?.voice.latency_ms || 7.2,
                }))}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <XAxis dataKey="time" tick={false} stroke="var(--color-hairline)" />
                <YAxis stroke="var(--color-hairline)" tick={{ fill: 'var(--color-ink-subtle)', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--color-surface-2)',
                    borderColor: 'var(--color-hairline-strong)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '12px',
                  }}
                />
                <Line type="monotone" dataKey="qos_off_lat" stroke="#e5484d" strokeWidth={2} dot={false} name="QoS OFF Latency (ms)" />
                <Line type="monotone" dataKey="qos_on_lat" stroke="var(--color-primary)" strokeWidth={2.5} dot={false} name="QoS ON Latency (ms)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};
