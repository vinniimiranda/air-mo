# Alerta de ar-condicionado quente e frio (Telegram)

Roda no **GitHub Actions** a cada 15 minutos: lê as mensagens novas dos grupos/canais de ofertas
e avisa quando aparece **ar-condicionado quente e frio com 9.000 BTUs ou mais**. Não precisa de
computador ligado.

A leitura usa **sua conta do Telegram** (um bot comum não consegue ler grupos/canais de terceiros).
O aviso chega por um bot seu (com notificação) ou, sem bot, nas suas "Mensagens salvas".

## Configuração (uma vez só, tudo pelo navegador)

### 1. Credenciais da API do Telegram
Em https://my.telegram.org → *API development tools*, crie um app e anote `api_id` e `api_hash`.

### 2. Gerar a sessão (login) num Codespace
No GitHub, neste repositório: **Code → Codespaces → Create codespace**. No terminal que abrir:
```bash
pip install -r requirements.txt && python gerar_sessao.py
```
Informe api_id e api_hash. Vai aparecer um QR code: no celular, abra Telegram → Configurações →
Dispositivos → **Conectar dispositivo desktop** e escaneie. Copie a sessão gerada. Depois apague o codespace (github.com/codespaces).

> ⚠️ A sessão dá acesso total à sua conta. Guarde só como *secret*, nunca no código.

### 3. Bot para receber os avisos (opcional, recomendado)
Crie um bot no @BotFather (guarde o token), mande `/start` para ele e pegue seu ID no @userinfobot.

### 4. Secrets do repositório
**Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Valor |
|---|---|
| `TG_API_ID` | api_id |
| `TG_API_HASH` | api_hash |
| `TG_SESSION` | sessão gerada no passo 2 |
| `TG_CHATS` | grupos/canais separados por vírgula, ex.: `@canal1,@grupo2` (ou IDs numéricos) |
| `BOT_TOKEN` | token do bot (opcional) |
| `ALERT_CHAT_ID` | seu ID numérico (opcional) |

Opcional, na aba **Variables**: `BTU_MINIMO` (padrão 9000) e `PRECO_MAXIMO` (ex.: 2500).

### 5. Testar
Aba **Actions → Alerta ar-condicionado → Run workflow**. Depois disso ele roda sozinho.

## Observações
- Repositório **privado** tem 2.000 min/mês grátis de Actions; a cada 15 min dá ~2.900 min.
  Nesse caso mude o cron em `.github/workflows/alerta.yml` para `*/30 * * * *`.
  Repositório **público** não tem limite (os secrets continuam protegidos).
- O GitHub pode atrasar execuções agendadas em alguns minutos.
- Em repositório público, agendamentos são pausados após 60 dias sem commits; o GitHub avisa
  por e-mail e basta reativar na aba Actions.

## Filtro (`filtro.py`)
- Precisa citar ar-condicionado/split **e** quente e frio (`quente e frio`, `quente/frio`, `Q/F`, `ciclo reverso`...).
- BTUs em formatos como `9000`, `9.000`, `12 000`, `9k`, `9 mil` + `BTU/BTUs/BTU/h`.
- `PRECO_MAXIMO` usa o menor `R$` da mensagem ("de X por Y").
- A mesma oferta repostada em 24h gera um único alerta.

Testes: `pip install pytest && pytest test_filtro.py`
