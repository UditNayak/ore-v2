# syntax=docker/dockerfile:1
# Development image: runs the Vite dev server with hot reload.
FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
