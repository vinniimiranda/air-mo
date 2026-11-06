"""Gera a TG_SESSION (login da sua conta) para usar como secret no GitHub.
Rode uma única vez, por exemplo num GitHub Codespace:  python gerar_sessao.py"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("TG_API_ID: "))
api_hash = input("TG_API_HASH: ").strip()
with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nCopie a linha abaixo e salve como secret TG_SESSION (NÃO compartilhe):\n")
    print(client.session.save())
