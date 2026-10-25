import { create } from 'zustand';
import { MetricSnapshot, FlowItem, PoliciesData, AuditEvent, ScenarioReport, MeterInfo, MLClassifierInfo } from '../types';
import {
  INITIAL_MOCK_POLICIES,
  INITIAL_MOCK_FLOWS,
  INITIAL_MOCK_EVENTS,
  INITIAL_MOCK_METERS,
  INITIAL_MOCK_ML_INFO,
  generateMockSnapshot,
} from '../mockData';

interface QoSState {
  activeTab: 'overview' | 'flows' | 'policies' | 'events' | 'demo' | 'about';
  connected: boolean;
  useMock: boolean;
  connectionStatus: {
    backend: boolean;
    controller: boolean;
    mininet: boolean;
  };
  isLoading: boolean;
  errorMessage: string | null;
  telemetry: MetricSnapshot;
  history: MetricSnapshot[];
  flows: FlowItem[];
  policies: PoliciesData;
  events: AuditEvent[];
  meters: MeterInfo[];
  mlMode: boolean;
  mlInfo: MLClassifierInfo | null;
  scenarioRunning: boolean;
  scenarioElapsed: number;
  report: ScenarioReport | null;

  // Actions
  setActiveTab: (tab: QoSState['activeTab']) => void;
  setUseMock: (mock: boolean) => void;
  setTelemetry: (snap: MetricSnapshot) => void;
  toggleQoS: () => Promise<void>;
  toggleMLMode: (enabled: boolean) => Promise<void>;
  fetchClassifierStatus: () => Promise<void>;
  fetchMeters: () => Promise<void>;
  switchPreset: (preset: string) => Promise<void>;
  updatePolicy: (profileName: string, className: string, key: string, value: number) => void;
  savePolicies: () => Promise<boolean>;
  startScenario: (qosEnabled: boolean) => Promise<void>;
  runBenchmark: () => Promise<void>;
  stopScenario: () => Promise<void>;
  fetchReport: () => Promise<void>;
  fetchData: () => Promise<void>;
  dismissError: () => void;
}

let mockTimer: any = null;
let mockStep = 0;

export const useQoSStore = create<QoSState>((set, get) => ({
  activeTab: 'overview',
  connected: false,
  useMock: (import.meta as any).env?.VITE_USE_MOCK === 'true',
  connectionStatus: {
    backend: false,
    controller: false,
    mininet: false,
  },
  isLoading: false,
  errorMessage: null,
  telemetry: generateMockSnapshot(0, true),
  history: Array.from({ length: 30 }, (_, i) => generateMockSnapshot(i, true)),
  flows: INITIAL_MOCK_FLOWS,
  policies: INITIAL_MOCK_POLICIES,
  events: INITIAL_MOCK_EVENTS,
  meters: INITIAL_MOCK_METERS,
  mlMode: false,
  mlInfo: INITIAL_MOCK_ML_INFO,
  scenarioRunning: false,
  scenarioElapsed: 0,
  report: null,

  setActiveTab: (activeTab) => set({ activeTab }),

  setUseMock: (useMock) => {
    set({ useMock });
    if (useMock) {
      if (!mockTimer) {
        mockTimer = setInterval(() => {
          mockStep++;
          const snap = generateMockSnapshot(mockStep, get().policies.qos_enabled);
          get().setTelemetry(snap);
          if (get().scenarioRunning) {
            set((s) => ({ scenarioElapsed: s.scenarioElapsed + 1 }));
          }
        }, 1000);
      }
    } else {
      if (mockTimer) {
        clearInterval(mockTimer);
        mockTimer = null;
      }
    }
  },

  setTelemetry: (snap: MetricSnapshot) => {
    set((state) => {
      const newHistory = [...state.history, snap];
      if (newHistory.length > 60) newHistory.shift();

      let updatedEvents = state.events;
      if (snap.events && snap.events.length > 0) {
        const existingMessages = new Set(state.events.map((e) => e.message));
        const newEvents: AuditEvent[] = [];
        for (const ev of snap.events) {
          if (!existingMessages.has(ev.message)) {
            newEvents.push({
              timestamp: typeof ev.timestamp === 'number' ? ev.timestamp : Date.now() / 1000,
              event_type: (ev.type as any) || 'ADAPTATION',
              message: ev.message,
              reason: ev.reason,
              before_value: (ev as any).before_value,
              after_value: (ev as any).after_value,
              source: 'live_telemetry',
            });
          }
        }
        if (newEvents.length > 0) {
          updatedEvents = [...newEvents, ...state.events];
        }
      }

      return {
        telemetry: snap,
        history: newHistory,
        events: updatedEvents,
      };
    });
  },

  toggleQoS: async () => {
    const nextVal = !get().policies.qos_enabled;
    set((state) => ({
      policies: { ...state.policies, qos_enabled: nextVal },
    }));

    if (get().useMock) {
      return;
    }

    try {
      await fetch('/api/policies', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          active_profile: get().policies.active_profile,
          qos_enabled: nextVal,
        }),
      });
    } catch (e) {
      console.warn('Backend unavailable; continuing in local state', e);
    }
  },

  switchPreset: async (preset: string) => {
    set((state) => ({
      policies: { ...state.policies, active_profile: preset },
    }));

    if (get().useMock) return;

    try {
      const res = await fetch(`/api/policies/preset/${preset}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        set({ policies: data });
      }
    } catch (e) {
      console.warn('Could not switch preset on backend', e);
    }
  },

  updatePolicy: (profileName: string, className: string, key: string, value: number) => {
    set((state) => {
      const p = { ...state.policies };
      if (p.profiles[profileName]?.classes[className]) {
        (p.profiles[profileName].classes[className] as any)[key] = value;
      }
      return { policies: p };
    });
  },

  savePolicies: async () => {
    if (get().useMock) return true;
    try {
      const res = await fetch('/api/policies', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          active_profile: get().policies.active_profile,
          qos_enabled: get().policies.qos_enabled,
          profiles: get().policies.profiles,
        }),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  startScenario: async (qosEnabled: boolean) => {
    set({ scenarioRunning: true, scenarioElapsed: 0 });
    if (get().useMock) {
      return;
    }
    try {
      await fetch('/api/scenario/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ qos_enabled: qosEnabled, duration_seconds: 65 }),
      });
    } catch (e) {
      console.warn('Could not start scenario on backend', e);
    }
  },

  stopScenario: async () => {
    set({ scenarioRunning: false });
    if (get().useMock) return;
    try {
      await fetch('/api/scenario/stop', { method: 'POST' });
    } catch (e) {
      console.warn('Could not stop scenario on backend', e);
    }
  },

  fetchReport: async () => {
    if (get().useMock) {
      // Return realistic synthetic comparison report
      const baselineTrajectory = Array.from({ length: 65 }, (_, i) => generateMockSnapshot(i, false));
      const qosTrajectory = Array.from({ length: 65 }, (_, i) => generateMockSnapshot(i, true));
      set({
        report: {
          timestamp: Date.now() / 1000,
          baseline_off: {
            qos_enabled: false,
            duration_seconds: 65,
            avg_voice_latency_ms: 124.6,
            max_voice_latency_ms: 220.4,
            avg_voice_jitter_ms: 42.8,
            avg_voice_loss_percent: 18.5,
            max_voice_loss_percent: 28.0,
          },
          qos_on: {
            qos_enabled: true,
            duration_seconds: 65,
            avg_voice_latency_ms: 7.3,
            max_voice_latency_ms: 8.1,
            avg_voice_jitter_ms: 0.9,
            avg_voice_loss_percent: 0.0,
            max_voice_loss_percent: 0.0,
          },
          improvement_percentages: {
            latency_reduction_percent: 94.1,
            jitter_reduction_percent: 97.9,
            loss_elimination_percent: 100.0,
          },
          baseline_trajectory: baselineTrajectory,
          qos_on_trajectory: qosTrajectory,
        },
      });
      return;
    }

    try {
      const res = await fetch('/api/scenario/report');
      if (res.ok) {
        const data = await res.json();
        set({ report: data });
      }
    } catch (e) {
      console.warn('Failed to fetch scenario report', e);
    }
  },

  toggleMLMode: async (enabled: boolean) => {
    set({ mlMode: enabled });
    if (get().useMock) {
      set((state) => ({
        mlInfo: state.mlInfo ? { ...state.mlInfo, ml_mode: enabled } : null,
      }));
      return;
    }
    try {
      await fetch('/api/classifier/mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ml_mode: enabled }),
      });
      get().fetchClassifierStatus();
    } catch (e) {
      console.warn('Failed to toggle ML mode', e);
    }
  },

  fetchClassifierStatus: async () => {
    if (get().useMock) return;
    try {
      const res = await fetch('/api/classifier/status');
      if (res.ok) {
        const data = await res.json();
        set({ mlMode: data.ml_mode, mlInfo: data });
      }
    } catch (e) {
      console.warn('Failed to fetch classifier status', e);
    }
  },

  fetchMeters: async () => {
    if (get().useMock) return;
    try {
      const res = await fetch('/api/meters');
      if (res.ok) {
        const data = await res.json();
        set({ meters: data });
      }
    } catch (e) {
      console.warn('Failed to fetch meter stats', e);
    }
  },

  runBenchmark: async () => {
    set({ scenarioRunning: true, scenarioElapsed: 0, isLoading: true });
    try {
      if (get().useMock) {
        await get().fetchReport();
        set({ scenarioElapsed: 65, scenarioRunning: false, isLoading: false });
        return;
      }
      await fetch('/api/scenario/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ qos_enabled: true, duration_seconds: 65 }),
      });
      await get().fetchReport();
      set({ scenarioRunning: false, isLoading: false });
    } catch (e: any) {
      set({ scenarioRunning: false, isLoading: false, errorMessage: 'Failed to run benchmark: ' + e?.message });
    }
  },

  dismissError: () => set({ errorMessage: null }),

  fetchData: async () => {
    set({ isLoading: true });
    try {
      const [policiesRes, flowsRes, eventsRes, classifierRes, metersRes] = await Promise.all([
        fetch('/api/policies'),
        fetch('/api/flows'),
        fetch('/api/events'),
        fetch('/api/classifier/status'),
        fetch('/api/meters'),
      ]);

      const isBackendLive = policiesRes.ok;
      const isControllerLive = classifierRes.ok;

      if (policiesRes.ok) set({ policies: await policiesRes.json() });
      if (flowsRes.ok) set({ flows: await flowsRes.json() });
      if (eventsRes.ok) set({ events: await eventsRes.json() });
      if (classifierRes.ok) {
        const cData = await classifierRes.json();
        set({ mlMode: cData.ml_mode, mlInfo: cData });
      }
      if (metersRes.ok) set({ meters: await metersRes.json() });

      set({
        connected: isBackendLive,
        connectionStatus: {
          backend: isBackendLive,
          controller: isControllerLive,
          mininet: isBackendLive && !get().useMock,
        },
        isLoading: false,
      });
    } catch {
      // Backend not running; activate mock automatically
      get().setUseMock(true);
      set({
        connected: false,
        connectionStatus: {
          backend: false,
          controller: false,
          mininet: false,
        },
        isLoading: false,
      });
    }
  },
}));
