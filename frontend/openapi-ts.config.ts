import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'http://localhost:8000/schema/',
  output: './src/lib/api-client',
  plugins: ['@hey-api/client-fetch'],
});
