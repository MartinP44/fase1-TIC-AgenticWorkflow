FROM node:18-alpine

WORKDIR /app

# Copy package files to leverage Docker caching
COPY package*.json ./
RUN npm install

# Copy frontend source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev"]
