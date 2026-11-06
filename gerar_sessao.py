"""Gera a TG_SESSION (login da sua conta) para usar como secret no GitHub.
Rode uma única vez, por exemplo num GitHub Codespace:  python gerar_sessao.py

Login por QR code: no celular, Telegram > Configurações > Dispositivos >
"Conectar dispositivo desktop" e escaneie o QR que aparece no terminal."""
import asyncio
import getpass

import qrcode
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession


def mostrar_qr(url: str):
    qr = qrcode.QRCode(border=2)
    qr.add_data(url)
    qr.print_ascii(invert=True)


async def main():
    api_id = int(input("TG_API_ID: "))
    api_hash = input("TG_API_HASH: ").strip()
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()

    qr_login = await client.qr_login()
    while True:
        print("\nNo celular: Telegram > Configurações > Dispositivos > Conectar dispositivo desktop")
        print("e escaneie o QR abaixo (se não der para ler, aumente o terminal ou diminua o zoom):\n")
        mostrar_qr(qr_login.url)
        try:
            await qr_login.wait(timeout=60)
            break
        except asyncio.TimeoutError:
            print("QR expirou, gerando outro...")
            await qr_login.recreate()
        except SessionPasswordNeededError:
            senha = getpass.getpass("Sua conta tem verificação em duas etapas. Senha do Telegram: ")
            await client.sign_in(password=senha)
            break

    print("\nLogin OK! Copie a linha abaixo e salve como secret TG_SESSION (NÃO compartilhe):\n")
    print(client.session.save())
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
