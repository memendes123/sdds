"""Plugin mínimo: força uso do bot Arkangel.

Objetivo: não fazer mais nada além de garantir que o Arkangel fique ativo.
"""


class plugin_arkangel_only:
    """Plugin enxuto para o sistema descrito no README do repositório."""

    def __init__(self):
        self._enabled = False

    def main(self, game_tick_packet, local_player_index, local_player_name):
        # Ativa Arkangel só uma vez para evitar chamadas repetidas desnecessárias.
        if not self._enabled:
            self.BotController("enable", botname="arkangel", source="plugin_arkangel_only")
            self._enabled = True

        # Retorno opcional conforme APIs de plugin que aceitam valor de status.
        return "arkangel_enabled"
