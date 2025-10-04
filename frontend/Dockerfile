# syntax=docker/dockerfile:1

FROM node:20-alpine AS builder
WORKDIR /app

# Ensure NODE_ENV is not set to production during build
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "run", "start"]
