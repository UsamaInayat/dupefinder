# DupeFinder Web (Vite + React) — production image for Railway
#
# Railway should use:
# - Root Directory: frontend-app
# - Dockerfile path: Dockerfile
#
# Build-time API base URL:
# - Pass VITE_API_BASE_URL as a Railway Variable (recommended), OR
# - pass --build-arg VITE_API_BASE_URL=... during docker build.

FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

FROM node:20-alpine AS runtime

WORKDIR /app

COPY --from=build /app/package.json /app/package-lock.json ./
RUN npm ci --omit=dev

COPY --from=build /app/dist ./dist

ENV PORT=8080

EXPOSE 8080

# Vite preview serves the production build. Bind 0.0.0.0 for containers.
CMD ["sh", "-c", "npm run preview -- --host 0.0.0.0 --port ${PORT:-8080}"]
