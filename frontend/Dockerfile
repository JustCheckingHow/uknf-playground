# syntax=docker/dockerfile:1

FROM node:20-alpine AS base
WORKDIR /app

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN npm install --legacy-peer-deps

# cache node_modules so we can hydrate bind-mounted volume later
RUN cp -R node_modules /opt/node_modules

COPY . .

RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]

FROM node:20-alpine AS dev
WORKDIR /app

COPY --from=base /opt/node_modules /opt/node_modules
COPY --from=base /app/package.json ./

# copy source after package manifest so live reload still works with bind mount
COPY . .

CMD ["npm", "run", "dev"]
