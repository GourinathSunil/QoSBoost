import { describe, it, expect } from 'vitest';
import { generateMockSnapshot, INITIAL_MOCK_POLICIES } from '../src/mockData';

describe('Frontend Smoke and Data Generation Tests', () => {
  it('generates compliant mock snapshots for QoS ON mode', () => {
    const snapOn = generateMockSnapshot(20, true);
    expect(snapOn.qos_enabled).toBe(true);
    expect(snapOn.voice.latency_ms).toBeLessThan(15.0);
    expect(snapOn.voice.loss_percent).toBe(0.0);
    expect(snapOn.voice.jitter_ms).toBeLessThan(3.0);
  });

  it('generates degraded metrics for QoS OFF mode during congestion', () => {
    const snapOff = generateMockSnapshot(25, false);
    expect(snapOff.qos_enabled).toBe(false);
    expect(snapOff.voice.latency_ms).toBeGreaterThan(50.0);
    expect(snapOff.voice.loss_percent).toBeGreaterThan(5.0);
  });

  it('contains valid default policy profiles matching design requirements', () => {
    expect(INITIAL_MOCK_POLICIES.profiles).toHaveProperty('Balanced');
    expect(INITIAL_MOCK_POLICIES.profiles).toHaveProperty('Voice-First');
    expect(INITIAL_MOCK_POLICIES.profiles).toHaveProperty('Video-Conference');

    const voiceClass = INITIAL_MOCK_POLICIES.profiles['Balanced'].classes['voice'];
    expect(voiceClass.priority).toBe(100);
    expect(voiceClass.queue_id).toBe(1);
    expect(voiceClass.dscp).toBe(46);
  });
});
