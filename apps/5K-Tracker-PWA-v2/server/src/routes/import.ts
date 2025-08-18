import { FastifyInstance } from 'fastify';
import { PrismaClient } from '@prisma/client';
import jwt from 'jsonwebtoken';
import { z } from 'zod';

const prisma = new PrismaClient();

// Middleware to authenticate JWT
async function authenticate(request: any, reply: any) {
  try {
    const authHeader = request.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return reply.code(401).send({ error: 'Missing or invalid authorization header' });
    }

    const token = authHeader.substring(7);
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any;
    request.user = decoded;
  } catch (error) {
    return reply.code(401).send({ error: 'Invalid token' });
  }
}

const importSchema = z.object({
  format: z.enum(['csv', 'json']),
  data: z.string(),
});

export async function importRoutes(fastify: FastifyInstance) {
  // Import races from V1 or CSV/JSON
  fastify.post('/', { preHandler: authenticate }, async (request: any, reply) => {
    try {
      const { format, data } = importSchema.parse(request.body);
      
      let races: any[] = [];
      
      if (format === 'json') {
        try {
          races = JSON.parse(data);
        } catch (e) {
          return reply.code(400).send({ error: 'Invalid JSON format' });
        }
      } else if (format === 'csv') {
        // Basic CSV parsing (in a real app, use a proper CSV parser)
        const lines = data.split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        
        races = lines.slice(1).filter(line => line.trim()).map(line => {
          const values = line.split(',').map(v => v.trim());
          const race: any = {};
          
          headers.forEach((header, index) => {
            const value = values[index];
            switch (header.toLowerCase()) {
              case 'date':
                race.date = new Date(value);
                break;
              case 'distance_km':
              case 'distance':
                race.distanceKm = parseFloat(value);
                break;
              case 'duration_sec':
              case 'duration':
                race.durationSec = parseInt(value);
                break;
              case 'location':
                race.location = value;
                break;
              case 'notes':
                race.notes = value;
                break;
              case 'weather':
                race.weather = value;
                break;
              case 'is_pr':
              case 'pr':
                race.isPr = value.toLowerCase() === 'true' || value === '1';
                break;
            }
          });
          
          return race;
        });
      }

      // Validate and import races
      const importedRaces = [];
      const errors = [];

      for (let i = 0; i < races.length; i++) {
        try {
          const race = races[i];
          
          // Basic validation
          if (!race.date || !race.distanceKm || !race.durationSec) {
            errors.push(`Row ${i + 1}: Missing required fields (date, distance, duration)`);
            continue;
          }

          // Calculate pace
          const paceSecPerKm = Math.round(race.durationSec / race.distanceKm);

          const createdRace = await prisma.race.create({
            data: {
              date: new Date(race.date),
              distanceKm: race.distanceKm,
              durationSec: race.durationSec,
              paceSecPerKm,
              isPr: race.isPr || false,
              location: race.location || null,
              weather: race.weather || null,
              notes: race.notes || null,
              region: race.region || null,
              userId: request.user.userId,
            },
          });

          importedRaces.push(createdRace);
        } catch (error) {
          errors.push(`Row ${i + 1}: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }

      return {
        message: `Import completed`,
        imported: importedRaces.length,
        errors: errors.length,
        errorDetails: errors,
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return reply.code(400).send({ error: 'Invalid input', details: error.issues });
      }
      fastify.log.error(error);
      return reply.code(500).send({ error: 'Internal server error' });
    }
  });
}