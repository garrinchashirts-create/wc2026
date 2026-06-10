# WC 2026 Analytics — Garrincha Shirts

🔗 **Live:** https://garrinchashirts-create.github.io/wc2026

Dashboard dinâmico com atualização automática 2x ao dia (08h e 20h BRT).

## Como funciona

```
GitHub Actions (08h e 20h BRT)
    │
    ├── scripts/fetch_data.py     → Odds (The Odds API) + Clima (Open-Meteo) + Notícias
    ├── scripts/generate_ai.py    → Claude gera value bets + prévias + análises táticas
    ├── scripts/build_index.py    → Monta o index.html final com tudo integrado
    └── index.html                → Publicado pelo GitHub Pages automaticamente
```

## Setup

### 1. Secrets necessários (Settings → Secrets → Actions)

| Secret | Valor | Onde obter |
|--------|-------|-----------|
| `ODDS_API_KEY` | `b3e388351ca7131ebb5a045ee7f5e4c8` | the-odds-api.com |
| `CLAUDE_API_KEY` | `sk-ant-...` | console.anthropic.com |

### 2. Ativar GitHub Pages
Settings → Pages → Source: **main** → **/ (root)** → Save

### 3. Atualização manual
Actions → **Update WC 2026 Dashboard** → **Run workflow**

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `index.html` | Dashboard final (gerado automaticamente) |
| `index_template.html` | Template base com placeholders `{{...}}` |
| `scripts/fetch_data.py` | Busca odds, clima e notícias |
| `scripts/generate_ai.py` | Gera conteúdo via Claude API |
| `scripts/build_index.py` | Monta o HTML final |
| `data/live_data.json` | Dados ao vivo (odds + clima + notícias) |
| `data/ai_content.json` | Conteúdo gerado por IA |

## Para atualizar scouts ou análises

Edite `index_template.html` → objeto `SCOUTS` ou `SW` no JavaScript.
O próximo build do GitHub Actions incorporará as mudanças.

## Estimativa de custos API (por mês)

| API | Uso | Custo |
|-----|-----|-------|
| The Odds API | ~60 req/mês (2x/dia) | Grátis (500/mês) |
| Open-Meteo | Ilimitado | Grátis |
| Claude API | ~60 chamadas/dia × 600 tokens | ~$3-8/mês |
| GitHub Actions | ~60 min/mês | Grátis |
