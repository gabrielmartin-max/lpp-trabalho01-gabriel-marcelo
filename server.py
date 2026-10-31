import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets": "client/assets",      # mapa, tileset e sprites da vila
})

# A partir da Etapa 1, adicione o seu código ABAIXO desta linha.

# ---------------------------------------------------------------------
# REGRAS DA VILA (as mesmas de docs/especificacao.md)
# ---------------------------------------------------------------------
CUSTO = 50  # litros de leite por queijaria
TEMPO_OBRA = 8  # segundos até a obra terminar
INTERVALO = 5  # segundos entre as ordenhas (produção automática)
GANHO_OBRA = 5  # litros a mais por ordenha quando uma queijaria termina

# O ESTADO mora no servidor: ele é a fonte da verdade.
estado = {
    "fase": "aguardando",  # aguardando -> aberta -> encerrada
    "leite": 150,  # litros de leite em estoque
    "trabalhadores": 0,  # ordenhadores ocupados agora
    "limite": 2,  # máximo de ordenhadores
    "producao": 10,  # litros produzidos a cada INTERVALO
    "intervalo": INTERVALO,
    "tempo_obra": TEMPO_OBRA,
    "custo": CUSTO,
    "concluidas": 0,
    "em_obra": 0,
}

jogadores = {}  # sid -> {"nome": ..., "papel": ...}


def fato(causa, **extras):
    """Monta o payload de um FATO: o estado atual, a CAUSA (o evento ou o
    temporizador que gerou o fato) e dados extras. O painel mostra a
    causa."""
    return {"estado": dict(estado), "causa": causa, **extras}


@sio.event
async def connect(sid, environ, auth):
    auth = auth or {}
    jogadores[sid] = {
        "nome": auth.get("nome", "Anônimo"),
        "papel": auth.get("papel", "jogador"),
    }
    # servidor -> UM cliente: só quem acabou de conectar precisa do estado
    await sio.emit("estado.sincronizado", fato("conexao"), to=sid)


@sio.event
async def disconnect(sid):
    jogadores.pop(sid, None)

async def recusar(sid, motivo, causa):
    """A recusa também é um EVENTO, e vai só para quem fez o pedido."""
    await sio.emit("operacao.recusada", {"motivo": motivo, "causa": causa}, to=sid)

@sio.on("vila.abertura_solicitada")  # PEDIDO do Mestre
async def abrir_vila(sid, dados=None):
    pedido = "vila.abertura_solicitada"
    
    if jogadores[sid]["papel"] != "mestre":
        await recusar(sid, "Só o Mestre pode abrir a temporada", pedido)
        return
        
    if estado["fase"] != "aguardando":
        await recusar(sid, "A temporada já foi aberta", pedido)
        return
        
    estado["fase"] = "aberta"
    await sio.emit("vila.iniciada", fato(pedido))  # FATO para todos


@sio.on("construcao.solicitada")  # PEDIDO do Jogador
async def construir(sid, dados=None):
    pedido = "construcao.solicitada"

    # Valide TUDO antes de alterar o estado e sem await no meio:
    # assim, dois pedidos simultâneos são decididos um de cada vez.
    if estado["fase"] != "aberta":
        motivo = "A temporada não está aberta"
    elif estado["leite"] < CUSTO:
        motivo = "Leite insuficiente"
    elif estado["trabalhadores"] >= estado["limite"]:
        motivo = "Sem ordenhador livre"
    else:
        motivo = None

    if motivo:
        await recusar(sid, motivo, pedido)  # só quem pediu recebe
        return

    estado["leite"] -= CUSTO
    estado["trabalhadores"] += 1
    estado["em_obra"] += 1
    nome = jogadores[sid]["nome"]
    await sio.emit("construcao.iniciada", fato(pedido, por=nome))  # FATO para todos
