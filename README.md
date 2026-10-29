# Pomodoro Blur (Windows)

Uma extensão leve e minimalista da Técnica Pomodoro para Windows inspirada no **GNOME Pomodoro**. Opera silenciosamente em segundo plano a partir da bandeja do sistema (*System Tray*), congelando as telas com um efeito suave de desfoque gaussiano (*frosted glass*) durante as pausas.

---

## Destaques

- **Zero poluição visual:** Sem janelas abertas na barra de tarefas ou no `Alt + Tab`. A aplicação opera 100% como utilitário de bandeja do sistema.
- **Técnica Pomodoro clássica:** 
  - Ciclos 1 a 3: 25 min de foco &rarr; 5 min de pausa curta.
  - Ciclo 4: 25 min de foco &rarr; 15 min de pausa longa.
  - Acompanhamento do progresso em tempo real (ex.: *Ciclo 2 de 4*).
- **Gatilho consciente de foco:** Ao término da pausa, a tela desfocada aguarda a sua confirmação (`Enter`, `Espaço` ou clique) para iniciar o próximo ciclo de foco, respeitando o princípio metodológico original.
- **Suporte multi-monitor diferenciado:**
  - **Monitor Principal:** Contagem regressiva de alta resolução e identificador do ciclo.
  - **Monitor Secundário:** Citações clássicas de sabedoria e reflexão (Marco Aurélio, Sêneca, Epicteto, Confúcio, Lao Tsé, Einstein) sorteadas sem repetição frequente.
  - Tipografia 100% branca e legível.
- **Ícones vetoriais Lucide:** Menu de contexto profissional e moderno sem emojis.
- **Desfoque nativo otimizado:** Captura instantânea e processamento bilinear/bicúbico ultrarrápido compatível com monitores Ultrawide e multi-display.
- **Persistência e inicialização:** Início automático opcional com o Windows via pasta de inicialização do usuário.

---

## Estrutura do Projeto

```
pomodoro-blur-win/
├── assets/
│   ├── Inter.ttf               # Tipografia principal (Inter)
│   ├── lucide.ttf              # Fonte de ícones Lucide
│   ├── lucide_glyphs.json      # Mapeamento unicode dos glifos
│   ├── quotes.json             # Banco de 70 pensamentos clássicos
│   ├── pomodoro.ico            # Ícone multi-resolução de foco
│   └── pomodoro_break.ico      # Ícone multi-resolução de pausa
├── config.json                 # Configurações de duração e preferências
├── iniciar.bat                 # Inicializador em segundo plano (sem janela preta)
├── run.bat                     # Inicializador com console de diagnóstico
├── main.py                     # Aplicação consolidada
├── requirements.txt            # Dependências Python
└── README.md
```

---

## Requisitos

- Windows 10 ou Windows 11
- Python 3.10 ou superior
- Dependências listadas em `requirements.txt`:
  - `PyQt6`
  - `Pillow`

---

## Instalação e Uso

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/jonatas07rocha/pomodoro-blur-win.git
   cd pomodoro-blur-win
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Inicie a aplicação:**
   - Dê dois cliques em `iniciar.bat` (ou execute `pythonw main.py`).
   - O ícone aparecerá imediatamente na bandeja do sistema ao lado do relógio do Windows.

---

## Atalhos e Controles

- **Clique esquerdo no ícone da bandeja:** Alterna entre Iniciar e Pausar o timer.
- **Clique direito no ícone da bandeja:** Abre o menu com presets de duração, configurações e teste de desfoque.
- **Durante a pausa (tela de desfoque):**
  - Pressione `Esc` ou clique na tela para retornar ao trabalho antecipadamente.
  - Ao zerar a pausa, pressione `Enter` ou `Espaço` para iniciar o próximo ciclo de foco.

---

## Licença

Distribuído sob a licença MIT. Consulte `LICENSE` para mais informações.
