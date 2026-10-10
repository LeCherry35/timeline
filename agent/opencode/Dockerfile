FROM node:22-slim

RUN npm install -g opencode-ai

WORKDIR /workspace
COPY opencode.json ./

EXPOSE 4096
CMD ["opencode", "serve", "--hostname", "0.0.0.0", "--port", "4096"]
