"""
========================================================================================
POMODORO BLUR - PONTO DE ENTRADA MULTIPLATAFORMA (WINDOWS & LINUX)
========================================================================================
Conceito:
- Utilitário de sistema em segundo plano (sem janelas na barra de tarefas ou Alt+Tab).
- Técnica Pomodoro fiel: 4 ciclos de foco com pausas curtas e uma pausa longa final.
- Suporte multi-monitor diferenciado:
    * Monitor Principal: Contagem regressiva limpa e indicador de ciclo.
    * Monitor Secundário: Citações clássicas de sabedoria (Marco Aurélio, Sêneca, etc.) sem repetição.
- Suporte nativo multiplataforma (Windows e distribuições Linux com X11/Wayland).
- Tipografia 100% branca na tela de pausa.
- Estilo minimalista puro, sem emojis.
========================================================================================
"""

import sys
from pomodoro import main

if __name__ == "__main__":
    main()
