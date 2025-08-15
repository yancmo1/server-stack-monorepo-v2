export class HealthKitWeb {
  async isAvailable() {
    return { available: false };
  }
  async requestAuthorization(_options: { read: string[]; write: string[] }) {
    // In web mode we simulate grant for easier local testing
    return { granted: true };
  }
  async saveWorkout(_options: { activityType: string; distanceMeters?: number; calories?: number; startDate: string; endDate: string }) {
    console.log('HealthKitWeb.saveWorkout called (mock)', _options);
    return { success: true };
  }
}
