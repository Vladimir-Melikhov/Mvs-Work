FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* yarn.lock* ./
RUN npm ci

COPY . .
RUN npm run build

FROM alpine:3.19
COPY --from=builder /app/dist /srv