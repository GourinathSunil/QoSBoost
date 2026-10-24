import React, { useState } from 'react';
import { useQoSStore } from '../store/useQoSStore';

interface NodeCoord {
  id: string;
  label: string;
  sublabel: string;
  x: number;
  y: number;
  type: 'host' | 'switch';
  role?: string;
}

export const TopologyGraph: React.FC = () => {
  const { telemetry, policies } = useQoSStore();
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const nodes: NodeCoord[] = [
    // Senders
    { id: 'h1', label: 'h1', sublabel: 'VoIP (100k)', x: 60, y: 50, type: 'host', role: 'voice' },
    { id: 'h2', label: 'h2', sublabel: 'Video (3.2M)', x: 60, y: 120, type: 'host', role: 'video' },
    { id: 'h3', label: 'h3', sublabel: 'Bulk 1 (TCP)', x: 60, y: 190, type: 'host', role: 'bulk' },
    { id: 'h4', label: 'h4', sublabel: 'Bulk 2 (TCP)', x: 60, y: 260, type: 'host', role: 'bulk' },
    { id: 'h5', label: 'h5', sublabel: 'Rogue UDP', x: 60, y: 330, type: 'host', role: 'flooder' },

    // Ingress Switch
    { id: 's1', label: 's1', sublabel: 'Ingress Edge', x: 260, y: 190, type: 'switch', role: 'ingress' },

    // Core Switches
    { id: 's2', label: 's2', sublabel: 'Bottleneck Core', x: 500, y: 100, type: 'switch', role: 'bottleneck' },
    { id: 's3', label: 's3', sublabel: 'Alternate Core', x: 500, y: 280, type: 'switch', role: 'alternate' },

    // Egress Switch
    { id: 's4', label: 's4', sublabel: 'Egress Edge', x: 740, y: 190, type: 'switch', role: 'egress' },

    // Receiver Host
    { id: 'h6', label: 'h6', sublabel: 'Media Sink', x: 920, y: 190, type: 'host', role: 'receiver' },
  ];

  const isRerouted = telemetry.rerouted;
  const util = telemetry.link_utilization;

  // Determine bottleneck link color
  const bottleneckColor = util > 80 ? '#e5484d' : util > 60 ? '#f76b15' : 'var(--color-primary)';
  const bottleneckWidth = Math.max(2, Math.min(6, (util / 100) * 6));

  const alternateColor = isRerouted ? 'var(--color-primary)' : 'var(--color-hairline-strong)';
  const alternateWidth = isRerouted ? 4 : 2;

  return (
    <div className="card-panel" style={{ padding: '20px', overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>Network Topology & QoS Forwarding Paths</span>
            <span className="badge" style={{ fontSize: '11px' }}>
              6 Hosts • 4 Switches
            </span>
          </div>
          <div className="caption" style={{ marginTop: '2px' }}>
            Dynamic OpenFlow 1.3 flow visualization showing HTB bottleneck (s1-s2) and QoS alternate route (s1-s3)
          </div>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--color-ink-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', backgroundColor: 'var(--color-primary)', display: 'inline-block' }} />
            <span>Active Real-Time Path ({isRerouted ? 's1→s3→s4' : 's1→s2→s4'})</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', backgroundColor: '#e5484d', display: 'inline-block' }} />
            <span>Bottleneck 10 Mbps (HTB Queues 0-3)</span>
          </div>
        </div>
      </div>

      <div style={{ position: 'relative', width: '100%', height: '380px', backgroundColor: 'var(--color-canvas)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-hairline)' }}>
        <svg width="100%" height="100%" viewBox="0 0 1000 380" style={{ overflow: 'visible' }}>
          <defs>
            {/* Animated packet flow gradient */}
            <linearGradient id="flowGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--color-primary)" stopOpacity="0.2" />
              <stop offset="50%" stopColor="var(--color-primary-hover)" stopOpacity="1" />
              <stop offset="100%" stopColor="var(--color-primary)" stopOpacity="0.2" />
            </linearGradient>

            {/* Glowing marker for bottleneck */}
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="var(--color-primary)" />
            </filter>
          </defs>

          {/* Links: Senders to Ingress s1 */}
          {['h1', 'h2', 'h3', 'h4', 'h5'].map((hId, idx) => {
            const h = nodes.find((n) => n.id === hId)!;
            const s1 = nodes.find((n) => n.id === 's1')!;
            return (
              <line
                key={`link-${hId}-s1`}
                x1={h.x + 20}
                y1={h.y + 15}
                x2={s1.x}
                y2={s1.y + 15}
                stroke="var(--color-hairline-strong)"
                strokeWidth={1.5}
              />
            );
          })}

          {/* Bottleneck Link: s1 to s2 (10 Mbps) */}
          <line
            x1={nodes.find((n) => n.id === 's1')!.x + 25}
            y1={nodes.find((n) => n.id === 's1')!.y}
            x2={nodes.find((n) => n.id === 's2')!.x - 10}
            y2={nodes.find((n) => n.id === 's2')!.y + 15}
            stroke={bottleneckColor}
            strokeWidth={bottleneckWidth}
            strokeDasharray={util > 80 ? '4 2' : undefined}
          />
          {/* Bottleneck Label */}
          <rect x="340" y="115" width="110" height="24" rx="4" fill="var(--color-surface-2)" stroke="var(--color-hairline)" />
          <text x="395" y="131" fill="var(--color-ink-muted)" fontSize="11" textAnchor="middle" fontFamily="var(--font-mono)">
            10M Bottleneck {util.toFixed(0)}%
          </text>

          {/* Alternate Link: s1 to s3 (20 Mbps) */}
          <line
            x1={nodes.find((n) => n.id === 's1')!.x + 25}
            y1={nodes.find((n) => n.id === 's1')!.y + 30}
            x2={nodes.find((n) => n.id === 's3')!.x - 10}
            y2={nodes.find((n) => n.id === 's3')!.y + 15}
            stroke={alternateColor}
            strokeWidth={alternateWidth}
          />
          <rect x="345" y="245" width="100" height="24" rx="4" fill="var(--color-surface-2)" stroke="var(--color-hairline)" />
          <text x="395" y="261" fill="var(--color-ink-muted)" fontSize="11" textAnchor="middle" fontFamily="var(--font-mono)">
            20M Alt Path (15ms)
          </text>

          {/* Core to Egress links: s2 to s4 & s3 to s4 */}
          <line
            x1={nodes.find((n) => n.id === 's2')!.x + 25}
            y1={nodes.find((n) => n.id === 's2')!.y + 15}
            x2={nodes.find((n) => n.id === 's4')!.x - 10}
            y2={nodes.find((n) => n.id === 's4')!.y}
            stroke={!isRerouted ? 'var(--color-primary)' : 'var(--color-hairline-strong)'}
            strokeWidth={!isRerouted ? 3 : 1.5}
          />
          <line
            x1={nodes.find((n) => n.id === 's3')!.x + 25}
            y1={nodes.find((n) => n.id === 's3')!.y + 15}
            x2={nodes.find((n) => n.id === 's4')!.x - 10}
            y2={nodes.find((n) => n.id === 's4')!.y + 30}
            stroke={isRerouted ? 'var(--color-primary)' : 'var(--color-hairline-strong)'}
            strokeWidth={isRerouted ? 3 : 1.5}
          />

          {/* Egress s4 to Receiver h6 */}
          <line
            x1={nodes.find((n) => n.id === 's4')!.x + 25}
            y1={nodes.find((n) => n.id === 's4')!.y + 15}
            x2={nodes.find((n) => n.id === 'h6')!.x}
            y2={nodes.find((n) => n.id === 'h6')!.y + 15}
            stroke="var(--color-primary)"
            strokeWidth={2.5}
          />

          {/* Render Nodes */}
          {nodes.map((n) => {
            const isSwitch = n.type === 'switch';
            const isHovered = hoveredNode === n.id;
            return (
              <g
                key={n.id}
                transform={`translate(${n.x}, ${n.y})`}
                onMouseEnter={() => setHoveredNode(n.id)}
                onMouseLeave={() => setHoveredNode(null)}
                style={{ cursor: 'pointer' }}
              >
                {/* Node Shape */}
                {isSwitch ? (
                  // Switch: Rounded Rectangle (DESIGN.md rounded.md 8px)
                  <rect
                    x="0"
                    y="0"
                    width="44"
                    height="32"
                    rx="8"
                    fill={isHovered ? 'var(--color-surface-3)' : 'var(--color-surface-2)'}
                    stroke={
                      n.id === 's2' && util > 80
                        ? '#e5484d'
                        : isHovered
                        ? 'var(--color-primary)'
                        : 'var(--color-hairline-strong)'
                    }
                    strokeWidth={isHovered ? 2 : 1.5}
                  />
                ) : (
                  // Host: Circular Node (rounded.full)
                  <circle
                    cx="15"
                    cy="15"
                    r="15"
                    fill={isHovered ? 'var(--color-surface-3)' : 'var(--color-surface-1)'}
                    stroke={
                      n.role === 'voice'
                        ? 'var(--color-primary)'
                        : n.role === 'video'
                        ? 'var(--color-brand-secure)'
                        : n.role === 'flooder'
                        ? '#e5484d'
                        : 'var(--color-hairline-strong)'
                    }
                    strokeWidth={isHovered ? 2 : 1.5}
                  />
                )}

                {/* Node ID Text */}
                <text
                  x={isSwitch ? 22 : 15}
                  y={isSwitch ? 20 : 19}
                  textAnchor="middle"
                  fill="var(--color-ink)"
                  fontSize="12"
                  fontWeight="600"
                  fontFamily="var(--font-sans)"
                >
                  {n.label}
                </text>

                {/* Sublabel below node */}
                <text
                  x={isSwitch ? 22 : 15}
                  y={isSwitch ? 45 : 42}
                  textAnchor="middle"
                  fill="var(--color-ink-subtle)"
                  fontSize="11"
                  fontFamily="var(--font-mono)"
                >
                  {n.sublabel}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Real-time Status Overlay on Canvas */}
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            backgroundColor: 'rgba(15, 16, 17, 0.85)',
            border: '1px solid var(--color-hairline)',
            borderRadius: 'var(--radius-sm)',
            padding: '6px 12px',
            fontSize: '12px',
            display: 'flex',
            gap: '16px',
            backdropFilter: 'blur(4px)',
          }}
        >
          <div>
            <span style={{ color: 'var(--color-ink-subtle)' }}>Active Route: </span>
            <span style={{ color: 'var(--color-ink)', fontWeight: 500 }}>{telemetry.path}</span>
          </div>
          <div>
            <span style={{ color: 'var(--color-ink-subtle)' }}>Bottleneck Util: </span>
            <span style={{ color: util > 80 ? '#e5484d' : 'var(--color-ink)', fontWeight: 500 }}>
              {util.toFixed(1)}%
            </span>
          </div>
          <div>
            <span style={{ color: 'var(--color-ink-subtle)' }}>Queue Mode: </span>
            <span style={{ color: policies.qos_enabled ? 'var(--color-semantic-success)' : 'var(--color-ink-subtle)', fontWeight: 500 }}>
              {policies.qos_enabled ? 'HTB Prioritized' : 'FIFO Default'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
