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