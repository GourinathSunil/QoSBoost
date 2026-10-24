export interface MetricSnapshot {
  timestamp: number;
  qos_enabled: boolean;
  phase: string;
  link_utilization: number;
  active_flows_count: number;
  voice: {
    latency_ms: number;
    jitter_ms: number;
    loss_percent: number;
    throughput_kbps: number;
  };
  video: {
    latency_ms: number;
    throughput_kbps: number;
    loss_percent: number;
  };
  bulk: {
    throughput_kbps: number;
  };
  flooder: {
    throughput_kbps: number;
    meter_drops?: number;
  };
  path: string;
  rerouted: boolean;
  events?: Array<{
    timestamp: number;
    type: string;
    message: string;
    reason?: string;
  }>;
}

export interface FlowItem {
  id: string;
  protocol: string;
  src_ip: string;
  src_port: number;
  dst_ip: string;
  dst_port: number;
  class_name: 'voice' | 'video' | 'web' | 'bulk';
  queue_id: number;
  path: string;
  rate_kbps: number;
  packets_count: number;
  bytes_count: number;
  decision: 'admit' | 'downgrade' | 'reject';
  last_seen: number;
}

export interface ClassPolicy {
  priority: number;
  min_rate_kbps: number;
  max_rate_kbps: number;
  target_latency_ms: number;
  target_jitter_ms: number;
  max_loss_percent: number;
  queue_id: number;
  dscp: number;
}

export interface PolicyProfile {
  name: string;
  description: string;
  classes: Record<string, ClassPolicy>;
}

export interface PoliciesData {
  active_profile: string;
  qos_enabled: boolean;
  profiles: Record<string, PolicyProfile>;
  dynamic_allocation: {
    high_watermark_utilization: number;
    low_watermark_utilization: number;
    step_down_bulk_percent: number;
    cooldown_seconds: number;
  };
  meters: Record<string, any>;
}

export interface AuditEvent {
  id?: number;
  timestamp: number;
  event_type: 'ADAPTATION' | 'METER_DROP' | 'ADMISSION' | 'REROUTE' | 'POLICY_UPDATE' | 'PRESET_SWITCH' | 'RECOVERY';
  message: string;
  reason?: string;
  before_value?: string;
  after_value?: string;
  source?: string;
}

export interface ScenarioReport {
  timestamp: number;
  baseline_off: {
    qos_enabled: boolean;
    duration_seconds: number;
    avg_voice_latency_ms: number;
    max_voice_latency_ms: number;
    avg_voice_jitter_ms: number;
    avg_voice_loss_percent: number;
    max_voice_loss_percent: number;
  };
  qos_on: {
    qos_enabled: boolean;
    duration_seconds: number;
    avg_voice_latency_ms: number;
    max_voice_latency_ms: number;
    avg_voice_jitter_ms: number;
    avg_voice_loss_percent: number;
    max_voice_loss_percent: number;
  };
  improvement_percentages: {
    latency_reduction_percent: number;
    jitter_reduction_percent: number;
    loss_elimination_percent: number;
  };
  baseline_trajectory: MetricSnapshot[];
  qos_on_trajectory: MetricSnapshot[];
}
