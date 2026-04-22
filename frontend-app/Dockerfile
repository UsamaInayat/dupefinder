# DupeFinder Web (Vite + React) — production image for Railway
#
# Railway should use:
# - Root Directory: frontend-app
# - Dockerfile path: Dockerfile
#
# Build-time API base URL:
# - Set `VITE_API_BASE` in Railway Variables (no trailing slash), OR
# - pass --build-arg VITE_API_BASE=... during docker build.
#
# Runtime uses `serve` to host prebuilt `dist/` (Vite is dev-only, not in production image).

FROM node:20-alpine AS build

WORKDIR /app

# `package-lock.json` must be in the repo (see root .gitignore: `!frontend-app/package-lock.json`) so `npm ci` works in CI/Railway.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE=""
ENV VITE_API_BASE=${VITE_API_BASE}

RUN npm run build

FROM node:20-alpine AS runtime

# Static file server; `vite` is not installed in prod (it's a devDependency).
RUN npm install -g serve@14.2.4

WORKDIR /app
COPY --from=build /app/dist ./dist

EXPOSE 8080
ENV PORT=8080

# Railway sets $PORT. `npm run preview` is wrong here: Vite is dev-only (not in prod node_modules).
CMD ["sh", "-c", "serve -s dist -l tcp://0.0.0.0:$PORT"]
