FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Copy node_modules (production dependencies only)
COPY node_modules ./node_modules

# Copy pre-built application
COPY dist ./dist

# Set the entrypoint
ENTRYPOINT ["node", "dist/index.js"]

# Default command shows help
CMD ["--help"]
