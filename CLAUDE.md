# Gestão de Apostas — contexto para o Claude

Projeto pessoal do Lucas: um app web para registrar as próprias apostas esportivas, usado no celular e no PC.
Converse com ele em português (pt-BR). Ele não é programador: explique em linguagem simples e não peça para ele editar código.

## O que é

- **Um único arquivo**: `index.html` (HTML + CSS + JS puros, sem build, sem framework).
- Bibliotecas por CDN: SheetJS 0.18.5 (cdnjs) para Excel/CSV e Firebase JS SDK **12.1.0** (gstatic) para login, banco e IA.
- Dados: `localStorage` no aparelho + **Firestore** do projeto Firebase `apostas-e3512` quando logado (e-mail/senha).
  A config do Firebase no HTML não é segredo (é pública por design no Firebase).
- Nasceu de um HTML antigo do Lucas (mesmo projeto Firebase e mesmo formato de dados) e de ideias do Pro Stake Manager (site pago que ele usa, ~2610 apostas lá).

## Telas (navegação inferior no celular, barra lateral no PC ≥1024px)

1. **Painel** — saldo da banca (R$ e unidades), placar Geral/Por mês, limites anti-tilt, pendentes com Green/Red em um toque, gráfico de resultado por dia/mês + tabela detalhada.
2. **Histórico** — busca, filtros (casa, esporte, resultado), abas por data, troca de status direto na lista, editar.
3. **Nova** — leitura do print do bilhete por IA, linha colada de outra IA (formato com `|`), ficha completa (simples/múltipla, R$ ou u, 7 resultados), prévia do lucro, avisos de limite com confirmação.
4. **Análise** — períodos, KPIs (lucro, ROI, acerto, fator de lucro, lucro/aposta, stake média, maior odd batida…), curva da banca com drawdown, tabela por casa/competição/esporte/mercado/tipster com renomear em massa.
5. **Banca e dados** — várias bancas, limites, saldo por casa (depósitos/saques), leitura de print (modelo Gemini), backup JSON, exportar Excel/CSV, importar planilha antiga / Excel / CSV do Pro Stake, lixeira (30 dias), login. (As ferramentas de EV, odd justa e surebet foram removidas a pedido do Lucas.)

## Modelo de dados (Firestore: `users/{uid}/...`)

- `bets/{id}`: `id, date (YYYY-MM-DD), competition, bookie, team1, team2, teams ("t1 x t2"), market, sport, tipster, notes, kind ('simples'|'multipla'), bankId, result, stake (R$), odd, cashout (R$, só em cashout), profit (R$), createdAt, updatedAt, deletedAt? (lixeira)`.
- `result`: `pendente | win | loss | halfwin | halfloss | void | cashout`. Lucro em `calcProfit()`.
- Unidades **não** são gravadas na ficha: `uOf()` divide o valor pelo valor da unidade **que valia quando a ficha foi registrada** (`unitValueAt(banca, createdAt)`). Cada banca guarda em `hist: [{until (ms), uv}]` os valores de unidade anteriores; ao salvar a banca com outro valor de unidade, o antigo entra no `hist` e só as fichas novas usam o novo. O saldo continua sendo `banca.amount + lucro de todas as fichas` (decisão do Lucas).
- `tombstones/{id}` `{deletedAt}`: exclusão definitiva, para outros aparelhos apagarem também.
- `settings/banks` `{list:[{id,name,amount,units,hist}], active}`, `settings/limits` `{stopDay, stopWeek, maxStake}` (em u, 0 = desligado), `settings/houses` `{txs:[{id,house,type:'dep'|'saq',amount,date}]}`, `settings/preferences` `{stakeMode, aiModel}`.
  O antigo `settings/bankroll` só é lido para migração.
- Sincronização: completa a cada 24 h, incremental (`updatedAt > último sync`) nas outras vezes. Ver `fullSyncFromCloud` / `incrementalSyncFromCloud`.
- Fichas antigas sem `bankId` pertencem à primeira banca.

## Leitura do print (IA)

- `window.cloudBets.readSlip()` usa **Firebase AI Logic** com `GoogleAIBackend` (Gemini Developer API, plano gratuito Spark), importando `firebase-ai.js` sob demanda.
- Modelo padrão e reservas em `AI_MODELS` (o app tenta o próximo se o modelo não existir). O Lucas pode trocar o nome em Banca → Leitura de print.
- Prompt em `slipPrompt()` pede JSON `{"apostas":[...]}` e passa as casas/competições que ele já usa, para manter os nomes iguais. Vários bilhetes no mesmo print viram uma fila (`slipQueue`).

## Situação (novembro de 2026)

Testado em Chrome headless (modo local, Firebase bloqueado): import da planilha antiga e do CSV do Pro Stake, registro, limites, Green/Red pelo painel, cashout, lixeira, várias bancas, backup/export, e a leitura de print com resposta **simulada**. Todos os cálculos conferidos.

**Ainda não testado de verdade / pendente:**
1. Sincronização real com o Firestore (login, sync entre celular e PC).
2. Chamada real ao Gemini: confirmar que `https://www.gstatic.com/firebasejs/12.1.0/firebase-ai.js` carrega e que o modelo padrão existe no plano gratuito. O Lucas precisa ativar no console: AI Logic → Começar → Gemini Developer API.
3. Regras de segurança do Firestore: garantir que cada usuário só lê/grava `users/{uid}/**` dele (inclui `settings/*` e `tombstones/*`).
4. Hospedagem: **no ar** pelo Firebase Hosting em `https://gestaodeapostas.web.app` (e também `https://apostas-e3512.web.app`, mesmo conteúdo). Publicar com `firebase deploy --only hosting` na raiz; o `firebase.json` envia só o `index.html` para os dois endereços. Falta: deploy automático pelo GitHub Actions e testar o login no endereço novo (se reclamar de domínio, adicionar em Authentication → Settings → Domínios autorizados).
5. App Check: **ligado no site** com reCAPTCHA Enterprise (chave do site em `APPCHECK_SITE_KEY` no `index.html`, registrada no App Check do projeto). A **exigência ainda não está aplicada** em nenhum serviço: acompanhar as métricas no console (App Check) por alguns dias e só então aplicar no AI Logic e no Firestore. Os testes locais não passam pelo App Check (domínio não autorizado na chave).
6. Opcional: manifest/ícone para "Adicionar à tela inicial"; desativar o cadastro de novas contas (Authentication → Configurações → Ações do usuário).

## Como testar

`tests/` tem testes Playwright (Python) que abrem o `index.html` com a internet bloqueada e o SheetJS servido localmente:

```
cd tests && npm install xlsx@0.18.5 && pip install playwright
python3 e2e.py        # fluxo geral (import, registro, limites, lixeira, telas)
python3 print_ia.py   # leitura do print com o Gemini simulado
```

Os testes usam o Chrome do sistema (`/usr/bin/google-chrome`); ajuste o caminho se for outro.

## Cuidados

- Não mude nomes de campos nem caminhos do Firestore sem migração: as apostas dele já estão lá.
- Datas são strings `YYYY-MM-DD` no fuso local (`todayISO()` usa a data local, não UTC).
- Planilhas: datas do Excel são lidas como número de série (sem `cellDates`) para não perder um dia por causa do fuso.
- Mantenha tudo num arquivo só, a menos que o Lucas peça outra estrutura.
