# 5K HealthKit Bridge (iOS)

Purpose: Wrap the existing 5K Tracker PWA as a native iOS app and add Apple HealthKit integration.

This folder contains a Capacitor shell. We leave the original PWA intact at `apps/5k-tracker-pwa`.

## High-level steps

1) Install JS deps

- From this folder:
  - npm install
  - (Optional) Set dev server in `capacitor.config.ts` to point to your running PWA (e.g., http://localhost:5001).

2) Create iOS project

- npx cap add ios
- npx cap open ios (opens Xcode)

3) Configure HealthKit in Xcode

- In Xcode, select the iOS target, go to Signing & Capabilities → "+ Capability" → add "HealthKit".
- Ensure your provisioning profile and bundle ID support HealthKit.
- In Info.plist, add NSHealthShareUsageDescription and NSHealthUpdateUsageDescription with user-facing reasons.

4) Implement native bridge (minimal outline)

- Create a Capacitor plugin (Objective-C/Swift) inside the iOS project or as a local plugin package. Suggested names:
  - Plugin name: `HealthKit`
  - Methods:
    - `isAvailable()` → returns whether Health is available on device
    - `requestAuthorization({ read: [HKQuantityTypeIdentifierDistanceWalkingRunning], write: [...] })`
    - `saveWorkout({ activityType, distanceMeters, calories, startDate, endDate })`
- Wire these to HealthKit APIs (HKHealthStore, HKQuantityTypeIdentifierDistanceWalkingRunning, HKWorkout).
- Keep the TypeScript interface in `src/healthkit.ts` in sync.

5) Build and run

- npx cap sync ios
- Build/run from Xcode on device (HealthKit requires real device, not simulator).

## Bridging your existing PWA

- Option A (dev): Point `server.url` in `capacitor.config.ts` at your running tracker (e.g., https://your-dev-host). The native app will load that URL.
- Option B (embed): Export or replicate minimal web shell (e.g., a landing + deeplink) and handle auth/nav into the PWA, or progressively migrate PWA views into this shell.

## Example TS usage

```ts
import { HealthKit } from './src/healthkit';

async function initHealth() {
  const { available } = await HealthKit.isAvailable();
  if (!available) return;

  const { granted } = await HealthKit.requestAuthorization({
    read: ['HKQuantityTypeIdentifierDistanceWalkingRunning'],
    write: []
  });

  if (granted) {
    await HealthKit.saveWorkout({
      activityType: 'running',
      distanceMeters: 5000,
      startDate: new Date().toISOString(),
      endDate: new Date().toISOString()
    });
  }
}
```

## Notes

- HealthKit calls must be on device and require explicit user permission.
- Keep the original PWA untouched; this wrapper is additive.
- If you later want to share code, consider a monorepo package for shared UI/logic.
