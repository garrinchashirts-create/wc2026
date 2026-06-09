/**
 * Cloudflare Worker — Proxy para Claude API
 * Garrincha Shirts WC 2026 Analytics
 *
 * COMO USAR:
 * 1. Acesse https://workers.cloudflare.com (conta gratuita)
 * 2. Crie um novo Worker
 * 3. Cole este código inteiro
 * 4. Substitua SUA_CHAVE_CLAUDE_AQUI pela sua chave da API Anthropic
 * 5. Clique em Deploy
 * 6. Copie a URL do Worker (ex: wc2026-proxy.seuusuario.workers.dev)
 * 7. No index.html, substitua a linha do fetch pelo URL do seu Worker
 */

// ⚠️  SUBSTITUA AQUI pela sua chave real da API Anthropic
// Obtenha em: https://console.anthropic.com
const CLAUDE_API_KEY = 'SUA_CHAVE_CLAUDE_AQUI';

// Domínios autorizados a usar este proxy (segurança)
const ALLOWED_ORIGINS = [
  'https://garrinchashirts-create.github.io',
  'https://www.garrinchashirts.com',
  'http://localhost',        // para testes locais
  'http://127.0.0.1',
];

const CORS_HEADERS = {
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
};

export default {
  async fetch(request) {
    const origin = request.headers.get('Origin') || '';
    const isAllowed = ALLOWED_ORIGINS.some(o => origin.startsWith(o));
    const corsOrigin = isAllowed ? origin : ALLOWED_ORIGINS[0];

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: { ...CORS_HEADERS, 'Access-Control-Allow-Origin': corsOrigin }
      });
    }

    // Only POST allowed
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': corsOrigin }
      });
    }

    try {
      const body = await request.json();

      // Forward to Claude API
      const claudeResponse = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': CLAUDE_API_KEY,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify(body),
      });

      const data = await claudeResponse.json();

      return new Response(JSON.stringify(data), {
        status: claudeResponse.status,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': corsOrigin,
        },
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': corsOrigin,
        },
      });
    }
  }
};
