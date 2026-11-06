from filtro import avaliar

def test_casos():
    ok = [
        "🔥 Ar Condicionado Split Inverter LG 12.000 BTUs Quente e Frio 220V\nR$ 2.399,00",
        "Ar-condicionado Samsung WindFree 9000 btu/h quente/frio por R$ 1.999",
        "SPLIT ELGIN ECO 18.000BTUS Q/F - de R$ 3.500,00 por R$ 2.799,90",
        "Ar condicionado Midea 9k btus Ciclo Reverso",
        "Ar Condicionado Gree 24 000 BTU Frio e Quente",
    ]
    nao = [
        "Ar Condicionado Split 12.000 BTUs Só Frio R$ 1.799",
        "Ar Condicionado Portátil 7.500 BTUs Quente e Frio",
        "Aquecedor elétrico quente e frio 9000 btus",  # não é ar-condicionado
        "Ventilador de teto",
    ]
    for t in ok:
        assert avaliar(t), t
    for t in nao:
        assert not avaliar(t), t
    assert avaliar(ok[2])["preco"] == 2799.90
    assert avaliar(ok[0])["btus"] == 12000
    assert avaliar(ok[0], preco_maximo=2000) is None
