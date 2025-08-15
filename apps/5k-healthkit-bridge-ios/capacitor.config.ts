import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.yourorg.fivektracker',
  appName: '5K Tracker',
  webDir: 'web',
  server: {
  // Point to the live PWA
  url: 'https://yancmo.xyz/tracker'
  }
};

export default config;
