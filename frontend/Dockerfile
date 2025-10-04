# syntax=docker/dockerfile:1

FROM node:20-alpine AS deps
WORKDIR /app

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN npm install --legacy-peer-deps

# cache node_modules so we can hydrate bind-mounted volume later
RUN cp -R node_modules /opt/node_modules

COPY . .

FROM deps AS builder
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS dev
WORKDIR /app

COPY --from=deps /opt/node_modules /opt/node_modules
COPY --from=deps /app/package*.json ./

# copy source after package manifest so live reload still works with bind mount
COPY . .

CMD ["npm", "run", "dev"]

FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=builder /app ./

EXPOSE 3000
CMD ["npm", "run", "start"]
