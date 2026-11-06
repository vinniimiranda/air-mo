"""Gera a TG_SESSION (login da sua conta) para usar como secret no GitHub.
Rode uma única vez, por exemplo num GitHub Codespace:  python gerar_sessao.py"""
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    api_id = int(input("TG_API_ID: "))
    api_hash = input("TG_API_HASH: ").strip()
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()  # pede telefone e o código enviado no seu Telegram
    print("\nCopie a linha abaixo e salve como secret TG_SESSION (NÃO compartilhe):\n")
    print(client.session.save())
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
