import { registerPlugin } from '@capacitor/core';

export interface HealthKitPlugin {
  isAvailable(): Promise<{ available: boolean }>;
  requestAuthorization(options: { read: string[]; write: string[] }): Promise<{ granted: boolean }>;
  saveWorkout(options: {
    activityType: string; // e.g., 'running'
    distanceMeters?: number;
    calories?: number;
    startDate: string; // ISO string
    endDate: string;   // ISO string
  }): Promise<{ success: boolean }>;
}

// Register plugin and provide a web implementation fallback that will be lazy-loaded.
export const HealthKit = registerPlugin<HealthKitPlugin>('HealthKit', {
  web: () => import('./healthkit.web').then(m => new m.HealthKitWeb())
});
