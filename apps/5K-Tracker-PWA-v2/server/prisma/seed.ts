import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('🌱 Starting seed...');

  // Create admin user
  const hashedPassword = await bcrypt.hash('admin123', 10);
  const adminUser = await prisma.user.upsert({
    where: { email: 'admin@5ktracker.com' },
    update: {},
    create: {
      email: 'admin@5ktracker.com',
      password: hashedPassword,
      name: 'Admin User',
      role: 'admin',
    },
  });

  // Create regular user
  const userPassword = await bcrypt.hash('user123', 10);
  const regularUser = await prisma.user.upsert({
    where: { email: 'john@example.com' },
    update: {},
    create: {
      email: 'john@example.com',
      password: userPassword,
      name: 'John Doe',
      role: 'user',
    },
  });

  // Create sample races for regular user
  const sampleRaces = [
    {
      date: new Date('2024-01-15'),
      distanceKm: 5.0,
      durationSec: 1392, // 23:12
      paceSecPerKm: 278,
      location: 'Central Park',
      weather: 'Sunny, 18°C',
      notes: 'Great run today! Felt strong throughout.',
      isPr: false,
    },
    {
      date: new Date('2024-01-10'),
      distanceKm: 10.0,
      durationSec: 2910, // 48:30
      paceSecPerKm: 291,
      location: 'Brooklyn Bridge',
      weather: 'Overcast, 15°C',
      notes: 'First 10K of the year. Struggled a bit in the second half.',
      isPr: true,
    },
    {
      date: new Date('2024-01-05'),
      distanceKm: 5.0,
      durationSec: 1365, // 22:45
      paceSecPerKm: 273,
      location: 'Prospect Park',
      weather: 'Clear, 12°C',
      notes: 'New PR! Perfect pacing strategy.',
      isPr: true,
    },
    {
      date: new Date('2023-12-20'),
      distanceKm: 21.0975,
      durationSec: 6135, // 1:42:15
      paceSecPerKm: 291,
      location: 'NYC Half Marathon',
      weather: 'Cool, 8°C',
      notes: 'Half marathon PR! Training paid off.',
      isPr: true,
    },
    {
      date: new Date('2023-12-15'),
      distanceKm: 5.0,
      durationSec: 1410, // 23:30
      paceSecPerKm: 282,
      location: 'Riverside Park',
      weather: 'Rainy, 10°C',
      notes: 'Tough conditions but finished strong.',
      isPr: false,
    },
  ];

  for (const race of sampleRaces) {
    await prisma.race.create({
      data: {
        ...race,
        userId: regularUser.id,
      },
    });
  }

  console.log('✅ Seed completed successfully!');
  console.log(`👤 Admin user: admin@5ktracker.com / admin123`);
  console.log(`👤 Regular user: john@example.com / user123`);
  console.log(`🏃 Created ${sampleRaces.length} sample races`);
}

main()
  .catch((e) => {
    console.error('❌ Seed failed:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });