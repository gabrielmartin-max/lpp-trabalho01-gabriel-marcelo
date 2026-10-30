# Especificação — Vila em Tempo Real

**Integrantes:** Gabriel Martin (@gabrielmartin-max) e Marcelo Schwartz (@marceloschwartz-si)
**Tipo de vila (sorteio):** Laticínios — leite → queijo

## 1. Regras da vila
- Recurso primário e recurso refinado: leite (em litros) → queijo.
- Estoque inicial: 150 L de leite e 0 queijos.
- Custo de uma construção: 50 L de leite por queijaria.
- Tempo da obra: 8 segundos.
- Limite de trabalhadores: 2 ordenhadores ocupados ao mesmo tempo. Cada obra ocupa 1 ordenhador até terminar.
- Produção automática: a cada 5 segundos a vila ordenha e o estoque ganha a produção atual (começa em 10 L).
- O que muda quando uma obra termina: o ordenhador fica livre, o número de queijarias prontas sobe em 1, a produção de leite aumenta em 5 L por ordenha e, a cada ordenha seguinte, cada queijaria pronta rende 1 queijo.
- O que expira (evento próprio): leite parado azeda. A cada 20 segundos, se o estoque passar de 100 L, 20 L azedam e saem do estoque.
- Quem pode o quê: só o Mestre abre e encerra a temporada; só com a temporada aberta se pode construir.
- Recusas: temporada fora do período aberto, leite insuficiente, nenhum ordenhador livre, ou jogador tentando abrir/encerrar a temporada. A recusa vai só para quem pediu e nada muda no estado.
- Ao encerrar a temporada, a produção, o azedamento e as obras em andamento param e novas ações são recusadas.

## 2. Eventos
| Evento | Emite | Recebe | O que muda no estado |
|---|---|---|---|
| `estado.sincronizado` | Servidor | Só quem entrou | Nada muda; quem entrou recebe o estado atual. |
| `vila.abertura_solicitada` | Mestre | Servidor | (é um pedido; nada muda) |
| `vila.iniciada` | Servidor | Todos | Temporada passa de "aguardando" para "aberta"; produção e azedamento começam. |
| `construcao.solicitada` | Jogador | Servidor | (é um pedido; nada muda) |
| `construcao.iniciada` | Servidor | Todos | Leite −50 L, ordenhadores ocupados +1, obras em andamento +1. |
| `operacao.recusada` | Servidor | Só quem pediu | Nada muda; o pedido é recusado com o motivo. |
| `recurso.produzido` | Servidor | Todos | Leite sobe pela produção atual; queijo sobe 1 por queijaria pronta. |
| `construcao.concluida` | Servidor | Todos | Ordenhador livre (−1), obras em andamento −1, queijarias prontas +1, produção de leite +5 L. |
| `leite.azedou` | Servidor | Todos | Leite −20 L (só se o estoque passar de 100 L). |
| `vila.encerramento_solicitado` | Mestre | Servidor | (é um pedido; nada muda) |
| `vila.encerrada` | Servidor | Todos | Temporada passa de "aberta" para "encerrada"; tudo para. |

## 3. Cenários de teste (Dado / Quando / Então, escritos com eventos)

### Recusa
Dado que a temporada está aberta e os 2 ordenhadores estão ocupados, quando o jogador A emite `construcao.solicitada`, então o servidor emite `operacao.recusada` apenas para A, com o motivo "Sem ordenhador livre"; o leite e os ordenhadores não mudam e ninguém mais recebe nada.

### Passagem do tempo
Dado que a temporada está aberta, com 150 L de leite e uma obra iniciada, quando passam 5 segundos, então o servidor emite `recurso.produzido` para todos (causa: temporizador) e o leite sobe 10 L; quando a obra completa 8 segundos, o servidor emite `construcao.concluida` para todos, o ordenhador fica livre e a produção passa a 15 L. Dado que o estoque está acima de 100 L, quando passam 20 segundos, então o servidor emite `leite.azedou` para todos e o leite cai 20 L.

### Disputa entre dois jogadores
Dado que há 1 de 2 ordenhadores ocupados e leite suficiente para uma obra, quando os jogadores A e B emitem `construcao.solicitada` ao mesmo tempo, então o servidor emite `construcao.iniciada` para todos referente a um deles e `operacao.recusada` (motivo "Sem ordenhador livre") apenas para o outro; os ordenhadores ocupados nunca passam de 2.