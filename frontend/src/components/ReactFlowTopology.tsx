import React, { useMemo } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  Handle,
  Position,
  NodeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useQoSStore } from '../store/useQoSStore';

// Custom Node for Switches (DESIGN.md rounded.md 8px, surface-2, hairline border)
const SwitchNode: React.FC<NodeProps> = ({ data }) => {
  const isBottleneck = data.role === 'bottleneck';
  const util = Number(data.utilization || 0);
  const isCongested = isBottleneck && util > 80;

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface-2)',
        border: `1.5px solid ${isCongested ? '#e5484d' : 'var(--color-hairline-strong)'}`,
        borderRadius: 'var(--radius-md)',
        padding: '10px 14px',
        minWidth: '110px',
        textAlign: 'center',
        boxShadow: isCongested ? '0 0 10px rgba(229, 72, 77, 0.4)' : undefined,
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: 'var(--color-primary)' }} />
      <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-ink)' }}>{data.label as string}</div>
      <div className="font-mono caption" style={{ color: 'var(--color-ink-subtle)', marginTop: '2px' }}>
        {data.sublabel as string}
      </div>
      {isBottleneck && (
        <div className="badge" style={{ marginTop: '4px', fontSize: '10px', padding: '1px 6px' }}>
          HTB Q0-Q3
        </div>
      )}
      <Handle type="source" position={Position.Right} style={{ background: 'var(--color-primary)' }} />
    </div>
  );
};

// Custom Node for Hosts (Circular, DESIGN.md rounded.full)
const HostNode: React.FC<NodeProps> = ({ data }) => {
  const role = data.role as string;
  const isVoice = role === 'voice';
  const isVideo = role === 'video';
  const isFlooder = role === 'flooder';

  const borderColor = isVoice
    ? 'var(--color-primary)'
    : isVideo
    ? 'var(--color-brand-secure)'
    : isFlooder
    ? '#e5484d'
    : 'var(--color-hairline-strong)';

  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface-1)',
        border: `1.5px solid ${borderColor}`,
        borderRadius: 'var(--radius-md)',
        padding: '8px 12px',
        minWidth: '95px',
        textAlign: 'center',
      }}
    >
      <Handle type="target" position={Position.Left} style={{ background: 'var(--color-primary)' }} />
      <div style={{ fontWeight: 600, fontSize: '12px', color: 'var(--color-ink)' }}>{data.label as string}</div>
      <div className="font-mono caption" style={{ color: 'var(--color-ink-subtle)', fontSize: '10px' }}>
        {data.sublabel as string}
      </div>
      <Handle type="source" position={Position.Right} style={{ background: 'var(--color-primary)' }} />
    </div>
  );
};

const nodeTypes = {
  switchNode: SwitchNode,
  hostNode: HostNode,
};

export const ReactFlowTopology: React.FC = () => {
  const { telemetry, policies } = useQoSStore();
  const util = telemetry.link_utilization;
  const isRerouted = telemetry.rerouted;

  const bottleneckColor = util > 80 ? '#e5484d' : util > 60 ? '#f76b15' : 'var(--color-primary)';
  const bottleneckWidth = Math.max(2, Math.min(5, (util / 100) * 5));

  // Compute Nodes
  const initialNodes: Node[] = useMemo(
    () => [
      // Senders
      { id: 'h1', type: 'hostNode', position: { x: 30, y: 30 }, data: { label: 'h1: VoIP', sublabel: '10.0.0.1 (100k)', role: 'voice' } },
      { id: 'h2', type: 'hostNode', position: { x: 30, y: 105 }, data: { label: 'h2: Video', sublabel: '10.0.0.2 (3.2M)', role: 'video' } },
      { id: 'h3', type: 'hostNode', position: { x: 30, y: 180 }, data: { label: 'h3: Bulk 1', sublabel: '10.0.0.3 (TCP)', role: 'bulk' } },
      { id: 'h4', type: 'hostNode', position: { x: 30, y: 255 }, data: { label: 'h4: Bulk 2', sublabel: '10.0.0.4 (TCP)', role: 'bulk' } },
      { id: 'h5', type: 'hostNode', position: { x: 30, y: 330 }, data: { label: 'h5: Rogue Flooder', sublabel: '10.0.0.5 (UDP)', role: 'flooder' } },

      // Ingress Switch
      { id: 's1', type: 'switchNode', position: { x: 230, y: 175 }, data: { label: 'Switch s1', sublabel: 'Ingress Edge', role: 'ingress' } },

      // Core Switches
      { id: 's2', type: 'switchNode', position: { x: 480, y: 80 }, data: { label: 'Switch s2', sublabel: 'Bottleneck (10M)', role: 'bottleneck', utilization: util } },
      { id: 's3', type: 'switchNode', position: { x: 480, y: 270 }, data: { label: 'Switch s3', sublabel: 'Alternate (20M)', role: 'alternate' } },

      // Egress Switch
      { id: 's4', type: 'switchNode', position: { x: 720, y: 175 }, data: { label: 'Switch s4', sublabel: 'Egress Edge', role: 'egress' } },

      // Receiver
      { id: 'h6', type: 'hostNode', position: { x: 920, y: 175 }, data: { label: 'h6: Sink', sublabel: '10.0.0.6 (Media)', role: 'receiver' } },
    ],
    [util]
  );

  // Compute Edges
  const initialEdges: Edge[] = useMemo(
    () => [
      // Senders to s1
      { id: 'e-h1-s1', source: 'h1', target: 's1', stroke: 'var(--color-hairline-strong)', animated: true },
      { id: 'e-h2-s1', source: 'h2', target: 's1', stroke: 'var(--color-hairline-strong)', animated: true },
      { id: 'e-h3-s1', source: 'h3', target: 's1', stroke: 'var(--color-hairline-strong)' },
      { id: 'e-h4-s1', source: 'h4', target: 's1', stroke: 'var(--color-hairline-strong)' },
      { id: 'e-h5-s1', source: 'h5', target: 's1', stroke: 'var(--color-hairline-strong)' },

      // s1 to s2 (Bottleneck link: 10 Mbps)
      {
        id: 'e-s1-s2',
        source: 's1',
        target: 's2',
        animated: true,
        style: { stroke: bottleneckColor, strokeWidth: bottleneckWidth },
        label: `10M (${util.toFixed(0)}%)`,
        labelStyle: { fill: 'var(--color-ink-subtle)', fontSize: 11, fontFamily: 'var(--font-mono)' },
      },

      // s1 to s3 (Alternate link: 20 Mbps)
      {
        id: 'e-s1-s3',
        source: 's1',
        target: 's3',
        animated: isRerouted,
        style: {
          stroke: isRerouted ? 'var(--color-primary)' : 'var(--color-hairline-strong)',
          strokeWidth: isRerouted ? 3.5 : 1.5,
        },
        label: isRerouted ? 'Rerouted Active' : '20M Alt',
        labelStyle: { fill: isRerouted ? 'var(--color-primary)' : 'var(--color-ink-subtle)', fontSize: 11 },
      },

      // s2 to s4 & s3 to s4
      {
        id: 'e-s2-s4',
        source: 's2',
        target: 's4',
        animated: !isRerouted,
        style: { stroke: !isRerouted ? 'var(--color-primary)' : 'var(--color-hairline-strong)', strokeWidth: !isRerouted ? 3 : 1.5 },
      },
      {
        id: 'e-s3-s4',
        source: 's3',
        target: 's4',
        animated: isRerouted,
        style: { stroke: isRerouted ? 'var(--color-primary)' : 'var(--color-hairline-strong)', strokeWidth: isRerouted ? 3 : 1.5 },
      },

      // s4 to h6
      { id: 'e-s4-h6', source: 's4', target: 'h6', animated: true, style: { stroke: 'var(--color-primary)', strokeWidth: 2.5 } },
    ],
    [bottleneckColor, bottleneckWidth, util, isRerouted]
  );

  return (
    <div className="card-panel" style={{ padding: '20px', overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>Network Topology Graph (React Flow)</span>
            <span className="badge" style={{ fontSize: '11px' }}>
              @xyflow/react
            </span>
          </div>
          <div className="caption" style={{ marginTop: '2px' }}>
            Interactive node graph with custom HTB switch nodes and animated utilization edges
          </div>
        </div>

        <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--color-ink-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', backgroundColor: 'var(--color-primary)', display: 'inline-block' }} />
            <span>Active Path: {telemetry.path}</span>
          </div>
        </div>
      </div>

      <div style={{ width: '100%', height: '410px', backgroundColor: 'var(--color-canvas)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-hairline)' }}>
        <ReactFlow
          nodes={initialNodes}
          edges={initialEdges}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Background color="var(--color-hairline)" gap={20} size={1} />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
};
