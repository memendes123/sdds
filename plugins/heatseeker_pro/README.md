# Heatseeker Pro Plugin (RLBot)

Plugin profissional base para modo **Heatseeker**, com foco em:
- defesa consistente,
- posicionamento inteligente entre bola e baliza,
- challenge controlado sem overcommit.

## Arquivo principal
- `plugin_heatseeker_pro.py`

## Estratégia aplicada
1. **Defensive line**: o bot calcula um alvo defensivo atrás da trajetória prevista da bola.
2. **Challenge window**: quando a bola entra em distância favorável, muda para ponto de interceptação.
3. **Recovery**: após challenge, prioriza retorno para zona defensiva.
4. **Boost discipline**: só usa boost quando alinhado ao alvo para evitar desperdício.

## Ajustes rápidos (tunables)
No arquivo Python, altere:
- `DEFENSIVE_DEPTH`
- `CHALLENGE_DISTANCE`
- `INTERCEPT_LOOKAHEAD_MIN` / `INTERCEPT_LOOKAHEAD_MAX`
- `JUMP_STRIKE_HEIGHT`

## Notas
- O comportamento foi pensado para ser robusto em ranked/casual Heatseeker sem depender de aerials avançados.
- Pode ser expandido com double-jump timing, dodge strike e predição de curva mais precisa da bola.
