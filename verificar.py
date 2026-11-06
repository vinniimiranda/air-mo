"""Roda uma checagem: lê as mensagens novas dos grupos/canais desde a última
execução e avisa sobre ofertas de ar-condicionado quente e frio >= 9.000 BTUs.
Feito para rodar agendado no GitHub Actions."""
import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from telethon import TelegramClient
from telethon.sessions import StringSession

from filtro import avaliar, normalizar

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("alerta")

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION = os.environ["TG_SESSION"]
# Um por linha (ou separados por vírgula): nome do grupo como aparece no Telegram,
# @username, link t.me/... ou ID numérico
_raw = os.environ["TG_CHATS"]
CHATS = [c.strip() for c in (_raw.splitlines() if "\n" in _raw else _raw.split(",")) if c.strip()]
BTU_MINIMO = int(os.getenv("BTU_MINIMO") or 9000)
PRECO_MAXIMO = float(os.environ["PRECO_MAXIMO"]) if os.getenv("PRECO_MAXIMO") else None
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALERT_CHAT_ID = os.getenv("ALERT_CHAT_ID")

ARQ_ESTADO = Path(os.getenv("ARQ_ESTADO", "estado/estado.json"))
JANELA_INICIAL = timedelta(hours=3)  # 1ª execução: olha só as últimas 3h
JANELA_DEDUP = 24 * 3600


def carregar_estado() -> dict:
    try:
        return json.loads(ARQ_ESTADO.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"ultimo_id": {}, "vistos": {}}


def salvar_estado(estado: dict):
    agora = time.time()
    estado["vistos"] = {h: t for h, t in estado["vistos"].items() if agora - t < JANELA_DEDUP}
    ARQ_ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ARQ_ESTADO.write_text(json.dumps(estado))


def hash_texto(texto: str) -> str:
    return hashlib.sha1(" ".join(normalizar(texto).split()).encode()).hexdigest()


def link_mensagem(chat, msg_id: int) -> str:
    if getattr(chat, "username", None):
        return f"https://t.me/{chat.username}/{msg_id}"
    return f"https://t.me/c/{chat.id}/{msg_id}"


def formatar_reais(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def enviar_alerta(client, texto: str):
    if BOT_TOKEN and ALERT_CHAT_ID:
        async with httpx.AsyncClient(timeout=20) as http:
            r = await http.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": ALERT_CHAT_ID, "text": texto},
            )
            if r.status_code == 200:
                return
            log.error("Falha ao enviar via bot (%s); enviando para Mensagens salvas", r.status_code)
    await client.send_message("me", texto)


def _eh_referencia_direta(ref: str) -> bool:
    return ref.startswith("@") or "t.me/" in ref or ref.lstrip("-").isdigit()


async def resolver_chats(client, refs: list[str]) -> list:
    """Converte cada referência em entidade; nomes são buscados nas suas conversas."""
    dialogos = None
    chats = []
    for ref in refs:
        if _eh_referencia_direta(ref):
            chats.append((ref, int(ref) if ref.lstrip("-").isdigit() else ref))
            continue
        if dialogos is None:
            dialogos = [d async for d in client.iter_dialogs() if d.is_group or d.is_channel]
        alvo = normalizar(ref).strip()
        exatos = [d for d in dialogos if normalizar(d.name).strip() == alvo]
        parciais = [d for d in dialogos if alvo in normalizar(d.name)]
        achados = exatos or parciais
        if not achados:
            log.error("Nenhum grupo/canal com o nome %r nas suas conversas", ref)
            continue
        if len(achados) > 1:
            log.warning("%r bate com vários: %s. Usando %r",
                        ref, [d.name for d in achados], achados[0].name)
        chats.append((ref, achados[0].entity))
    return chats


async def checar_chat(client, chat_ref, estado: dict) -> int:
    chat = chat_ref if not isinstance(chat_ref, (str, int)) else await client.get_entity(chat_ref)
    chave = str(chat.id)
    ultimo = estado["ultimo_id"].get(chave)
    if ultimo is None:
        corte = datetime.now(timezone.utc) - JANELA_INICIAL
        msgs = [m async for m in client.iter_messages(chat, limit=300) if m.date >= corte]
        msgs.reverse()
    else:
        msgs = [m async for m in client.iter_messages(chat, min_id=ultimo, reverse=True, limit=1000)]

    alertas = 0
    for m in msgs:
        texto = m.raw_text or ""
        res = avaliar(texto, BTU_MINIMO, PRECO_MAXIMO)
        if res:
            h = hash_texto(texto)
            if h not in estado["vistos"]:
                estado["vistos"][h] = time.time()
                preco = formatar_reais(res["preco"]) if res["preco"] else "não identificado"
                await enviar_alerta(client, (
                    "❄️🔥 Oferta de ar-condicionado quente/frio!\n"
                    f"Grupo: {getattr(chat, 'title', chat_ref)}\n"
                    f"BTUs: {res['btus']:,}".replace(",", ".") + "\n"
                    f"Preço: {preco}\n"
                    f"Link: {link_mensagem(chat, m.id)}\n\n"
                    f"{texto[:1500]}"
                ))
                alertas += 1
        estado["ultimo_id"][chave] = max(m.id, estado["ultimo_id"].get(chave, 0))
    if ultimo is None and not msgs:
        ultima = await client.get_messages(chat, limit=1)
        if ultima:
            estado["ultimo_id"][chave] = ultima[0].id
    log.info("%s: %d mensagem(ns) nova(s), %d alerta(s)", getattr(chat, "title", chat_ref), len(msgs), alertas)
    return alertas


async def main():
    estado = carregar_estado()
    async with TelegramClient(StringSession(SESSION), API_ID, API_HASH) as client:
        if not await client.is_user_authorized():
            raise SystemExit("TG_SESSION inválida ou expirada: gere de novo com gerar_sessao.py")
        for nome, chat_ref in await resolver_chats(client, CHATS):
            try:
                await checar_chat(client, chat_ref, estado)
            except Exception:
                log.exception("Erro ao checar %s", nome)
            finally:
                salvar_estado(estado)


if __name__ == "__main__":
    asyncio.run(main())
