# WC 2026 Analytics — Garrincha Shirts

Dashboard de análise e apostas para a Copa do Mundo 2026.

🔗 **Live:** https://garrinchashirts-create.github.io/wc2026

---

## Arquivos do repositório

| Arquivo | Descrição |
|---|---|
| `index.html` | Dashboard completo (abrir no browser) |
| `fetch_odds.py` | Script Python que busca odds da Copa |
| `odds_data.json` | Odds atualizadas pelo GitHub Actions |
| `cloudflare_worker.js` | Proxy para a API do Claude |
| `.github/workflows/update_odds.yml` | GitHub Action (roda todo dia 08h UTC) |

---

## Setup completo

### Passo 1 — Subir os arquivos no GitHub

1. Acesse **github.com/garrinchashirts-create**
2. Crie repositório `wc2026` (Public)
3. Faça upload de: `index.html`, `fetch_odds.py`, `odds_data.json`, `cloudflare_worker.js`
4. Crie `.github/workflows/update_odds.yml` (Add file → Create new file)

### Passo 2 — Ativar GitHub Pages

1. **Settings → Pages**
2. Source: **Deploy from branch**
3. Branch: **main** → **/ (root)**
4. **Save**
5. Aguarde 2 minutos → acesse: `garrinchashirts-create.github.io/wc2026`

### Passo 3 — Adicionar secret da The Odds API

1. **Settings → Secrets and variables → Actions → New repository secret**
2. Name: `ODDS_API_KEY`
3. Value: `b3e388351ca7131ebb5a045ee7f5e4c8`
4. **Add secret**

As odds serão atualizadas automaticamente todo dia às 08:00 UTC (05:00 BRT).
Para forçar atualização manual: **Actions → Update WC 2026 Odds → Run workflow**

### Passo 4 — Integrar o Claude (análise por IA)

#### 4a. Criar proxy no Cloudflare Workers (gratuito)

1. Acesse **https://workers.cloudflare.com** e crie uma conta gratuita
2. Clique em **Create a Worker**
3. Apague o código padrão e cole o conteúdo de `cloudflare_worker.js`
4. Substitua `SUA_CHAVE_CLAUDE_AQUI` pela sua chave da API Anthropic
   - Obtenha em: **https://console.anthropic.com → API Keys**
5. Clique em **Deploy**
6. Copie a URL do Worker (ex: `https://wc2026-proxy.garrinchashirts-create.workers.dev`)

#### 4b. Conectar o proxy ao dashboard

No `index.html`, encontre esta linha (aprox. linha 700):
```javascript
const PROXY_URL = 'https://wc2026-proxy.garrinchashirts-create.workers.dev';
```
Substitua pela URL real do seu Worker. Salve e faça commit.

---

## Como atualizar o dashboard

Para adicionar dados, editar scouts ou mudar qualquer coisa:

1. Acesse o arquivo no GitHub
2. Clique no ícone de lápis (Edit)
3. Faça a alteração
4. **Commit changes**

O GitHub Pages atualiza em ~1 minuto automaticamente.

---

## Estrutura dos dados

Para atualizar os scouts das seleções, edite o objeto `SCOUTS` no `index.html`:
```javascript
ESP:{name:"Espanha", rating:100, xG:2.95, xGA:0.88, pos:63.6, gm:3.00, gs:0.90, ...}
```

Para atualizar odds manualmente, edite `odds_data.json` ou dispare o workflow.
