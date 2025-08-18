import { FastifyInstance } from 'fastify';
import { PrismaClient } from '@prisma/client';
import jwt from 'jsonwebtoken';
import { z } from 'zod';

const prisma = new PrismaClient();

const createRaceSchema = z.object({
  date: z.string().datetime(),
  distanceKm: z.number().positive(),
  durationSec: z.number().positive(),
  paceSecPerKm: z.number().positive().optional(),
  isPr: z.boolean().default(false),
  region: z.string().optional(),
  location: z.string().optional(),
  weather: z.string().optional(),
  notes: z.string().optional(),
});

const updateRaceSchema = createRaceSchema.partial();

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

export async function runsRoutes(fastify: FastifyInstance) {
  // Get all runs for user (with pagination, filtering, sorting)
  fastify.get('/', { preHandler: authenticate }, async (request: any, reply) => {
    try {
      const { page = 1, limit = 20, sortBy = 'date', sortOrder = 'desc', search, distance } = request.query;
      
      const where: any = {
        userId: request.user.userId,
      };

      if (search) {
        where.OR = [
          { location: { contains: search, mode: 'insensitive' } },
          { notes: { contains: search, mode: 'insensitive' } },
        ];
      }

      if (distance) {
        where.distanceKm = parseFloat(distance);
      }

      const runs = await prisma.race.findMany({
        where,
        orderBy: { [sortBy]: sortOrder },
        skip: (page - 1) * limit,
        take: limit,
        include: {
          photos: true,
        },
      });

      const total = await prisma.race.count({ where });

      return {
        runs,
        pagination: {
          page,
          limit,
          total,
          pages: Math.ceil(total / limit),
        },
      };
    } catch (error) {
      fastify.log.error(error);
      return reply.code(500).send({ error: 'Internal server error' });
    }
  });

  // Get specific run
  fastify.get('/:id', { preHandler: authenticate }, async (request: any, reply) => {
    try {
      const { id } = request.params;
      
      const run = await prisma.race.findFirst({
        where: {
          id,
          userId: request.user.userId,
        },
        include: {
          photos: true,
        },
      });

      if (!run) {
        return reply.code(404).send({ error: 'Run not found' });
      }

      return run;
    } catch (error) {
      fastify.log.error(error);
      return reply.code(500).send({ error: 'Internal server error' });
    }
  });

  // Create new run
  fastify.post('/', { preHandler: authenticate }, async (request: any, reply) => {
    try {
      const data = createRaceSchema.parse(request.body);
      
      // Calculate pace if not provided
      const paceSecPerKm = data.paceSecPerKm || Math.round(data.durationSec / data.distanceKm);

      const run = await prisma.race.create({
        data: {
          ...data,
          date: new Date(data.date),
          paceSecPerKm,
          userId: request.user.userId,
        },
        include: {
          photos: true,
        },
      });

      return run;
    } catch (error) {
      if (error instanceof z.ZodError) {
        return reply.code(400).send({ error: 'Invalid input', details: error.issues });
      }
      fastify.log.error(error);
      return reply.code(500).send({ error: 'Internal server error' });
    }
  });

  // Update run
  fastify.put('/:id', { preHandler: authenticate }, async (request: any, reply) => {
    try {
      const { id } = request.params;
      const data = updateRaceSchema.parse(request.body);

      // Check ownership
      const existingRun = await prisma.race.findFirst({
        where: { id, userId: request.user.userId },
      });

      if (!existingRun) {
        return reply.code(404).send({ error: 'Run not found' });
      }

      // Recalculate pace if duration or distance changed
      const updateData: any = { ...data };
      if (data.date) {
        updateData.date = new Date(data.date);
      }
      if (data.durationSec || data.distanceKm) {
        const duration = data.durationSec || existingRun.durationSec;
        const distance = data.distanceKm || parseFloat(existingRun.distanceKm.toString());
        updateData.paceSecPerKm = Math.round(duration / distance);
      }

      const run = await prisma.race.update({
        where: { id },
        data: updateData,
        include: {
          photos: true,
        },
      });

      return run;
    } catch (error) {
      if (error instanceof z.ZodError) {
        return reply.code(400).send({ error: 'Invalid input', details: error.issues });
      }
      fastify.log.error(error);
      return reply.code(500).send({ error: 'Internal server error' });
    }
  });

  // Delete run
  fastify.delete('/:id', { preHandler: authenticate }, async (request: any, reply) => {
    try {
      const { id } = request.params;

      // Check ownership
      const existingRun = await prisma.race.findFirst({
        where: { id, userId: request.user.userId },
      });

      if (!existingRun) {
        return reply.code(404).send({ error: 'Run not found' });
      }

      await prisma.race.delete({
        where: { id },
      });

      return { message: 'Run deleted successfully' };
    } catch (error) {
      fastify.log.error(error);
      return reply.code(500).send({ error: 'Internal server error' });
    }
  });
}