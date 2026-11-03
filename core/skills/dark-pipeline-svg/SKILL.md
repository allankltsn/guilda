---
name: dark-pipeline-svg
description: Cria diagramas SVG animados e gráficos animados (barra empilhada de porcentagens, barras horizontais, donut) e banners de título de projeto (hero) com painel animado da stack, no design system dark pipeline (fundo #0b0f17, SMIL, código de cores por grupo) — Engineering Template style.
---

# Dark Pipeline SVG — Design System

Use este skill para criar diagramas SVG didáticos e detalhados no estilo do **Engineering Template**, com animações SMIL inline, tema dark e código de cores por grupo. Siga cada seção rigorosamente para manter consistência entre diagramas.

---

## 1. Estrutura do arquivo

Sempre gere um arquivo `.html` completo (não SVG puro) para garantir renderização correta:

```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SVG NN — Título do Diagrama</title>
<style>
  :root { color-scheme: dark }
  body {
    margin: 0; background: #0b0f17;
    display: flex; align-items: center; justify-content: center;
    min-height: 100%; padding: 40px 16px; box-sizing: border-box;
  }
  svg { width: 100%; max-width: 1800px; height: auto; display: block; }
</style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 800"
     font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif">
  <!-- conteúdo -->
</svg>
</body>
</html>
```

**viewBox padrão:** `0 0 1800 800`. Use `0 0 1800 830` ou maior se o diagrama precisar de mais altura.

---

## 2. Paleta de cores — código por função

| Token | Hex | Uso |
|-------|-----|-----|
| `BG` | `#0b0f17` | Fundo da página e do SVG |
| `SURFACE` | `#111827` | Header, footer, painéis de legenda |
| `NODE` | `#0d1117` | Nós/cards internos (cor base) |
| `BORDER` | `#1f2937` | Bordas neutras entre elementos |
| `TEXT` | `#e6edf3` | Texto principal |
| `SUBTEXT` | `#8b96a8` | Texto secundário / descrições |
| `MUTED` | `#4b5563` | Texto auxiliar, labels de código |
| **BLUE** `#3b82f6` | Setup, entrada, Grupo Eng | Etapas iniciais, backend/frontend |
| **TEAL** `#2dd4bf` | Execução ativa (pulsing) | CI/CD, worktrees, infra |
| **AMBER** `#f59e0b` | Gates, orquestrador | Decisões, planejamento, checkpoints |
| **GREEN** `#4ade80` | Aprovado, concluído | Done, SLO ok, aprovação |
| **VIOLET** `#7c3aed` / `#a78bfa` | Privacidade, suporte | LGPD, compliance |
| **PINK** `#f472b6` | Design & UX | Wireframes, branding, acessibilidade |
| **RED** `#ef4444` | Segurança, rejeição, crítico | ALERTA_PERIGO, bugs, falhas |

**Fills de nós por grupo:**
- Azul:   `fill="#0d1a2e" stroke="#3b82f6"`
- Teal:   `fill="#0d1a1a" stroke="#2dd4bf"`
- Amber:  `fill="#1a0f00" stroke="#f59e0b"`
- Green:  `fill="#0d1a0d" stroke="#4ade80"`
- Violet: `fill="#120a1e" stroke="#a78bfa"`
- Pink:   `fill="#1a0918" stroke="#f472b6"`
- Red:    `fill="#1a0a0a" stroke="#ef4444"`

---

## 3. Animações SMIL — padrões obrigatórios

### 3a. Fade-in sequencial de grupos (entrada)
```xml
<g opacity="0">
  <animate attributeName="opacity" to="1" begin="0.3s" dur="0.4s" fill="freeze"/>
  <!-- conteúdo do grupo -->
</g>
```
Escalone o `begin` em passos de `0.2s`–`0.4s` por bloco (0.1s, 0.3s, 0.5s, 0.7s…).

### 3b. Borda pulsante de nó ativo
```xml
<rect ... stroke="#2dd4bf" stroke-width="1.5">
  <animate attributeName="stroke-opacity" values="0.35;1;0.35" dur="2.5s" repeatCount="indefinite"/>
</rect>
```

### 3c. Dot animado em caminho (fluxo de dados)
```xml
<defs>
  <path id="flow-path" d="M100,200 C200,200 300,150 400,150" fill="none"/>
</defs>
<circle r="3.5" fill="#2dd4bf">
  <animateMotion dur="2s" repeatCount="indefinite">
    <mpath href="#flow-path"/>
  </animateMotion>
  <animate attributeName="opacity" values="0;1;1;0" dur="2s" repeatCount="indefinite"/>
</circle>
```
Use `dur` diferente por caminho (1.8s, 2.2s, 2.6s…) para evitar sincronismo.

### 3d. Dot em linha reta (timeline horizontal)
```xml
<circle r="4" fill="#f59e0b">
  <animate attributeName="cx" values="100;700" dur="4s" repeatCount="indefinite"/>
  <animate attributeName="opacity" values="0;1;1;0" dur="4s" repeatCount="indefinite"/>
</circle>
```

### 3e. Pulsing de círculo indicador no status bar
```xml
<circle cx="38" cy="683" r="4" fill="#2dd4bf">
  <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite"/>
</circle>
```

---

## 4. Markers de seta (sempre em `<defs>`)

Declare um marker por cor usada no diagrama:

```xml
<defs>
  <marker id="arr-teal" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto">
    <path d="M0,0 L8,3.5 L0,7 Z" fill="#2dd4bf"/>
  </marker>
  <marker id="arr-blue" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto">
    <path d="M0,0 L8,3.5 L0,7 Z" fill="#3b82f6"/>
  </marker>
  <marker id="arr-amber" markerWidth="8" markerHeight="7" refX="7" refY="3.5" orient="auto">
    <path d="M0,0 L8,3.5 L0,7 Z" fill="#f59e0b"/>
  </marker>
  <!-- repita para green, violet, pink, red conforme necessário -->
</defs>
```

Uso: `<line ... marker-end="url(#arr-teal)"/>`

---

## 5. Estrutura de layout

### Header (sempre presente)
```xml
<rect x="20" y="16" width="1760" height="48" rx="6" fill="#111827" stroke="#1f2937" stroke-width="1"/>
<!-- accent bar lateral com a cor do grupo -->
<rect x="20" y="16" width="6" height="48" rx="3" fill="ACCENT_COLOR"/>
<text x="44" y="37" font-size="15" font-weight="700" fill="#e6edf3">NN — Título do Diagrama</text>
<text x="44" y="55" font-size="11" fill="#8b96a8">subtítulo · palavras-chave · conceitos cobertos</text>
<text x="1760" y="37" font-size="9.5" fill="#4b5563" text-anchor="end"
      font-family="ui-monospace,...">ETAPA NN/17</text>
<text x="1760" y="52" font-size="9.5" fill="ACCENT_COLOR" text-anchor="end"
      font-family="ui-monospace,...">CATEGORIA</text>
```

### Status bar (sempre presente, y = altura-128)
```xml
<rect x="20" y="672" width="1760" height="22" rx="4" fill="#111827" stroke="#1f2937" stroke-width="1"/>
<circle cx="38" cy="683" r="4" fill="ACCENT_COLOR">
  <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" repeatCount="indefinite"/>
</circle>
<text x="50" y="687" font-size="9.5" fill="ACCENT_COLOR"
      font-family="ui-monospace,...">ETAPA NN</text>
<text x="..." y="687" font-size="9.5" fill="#8b96a8"
      font-family="ui-monospace,...">resumo · uma linha · do que está neste diagrama</text>
<text x="1770" y="687" font-size="9.5" fill="#4b5563" text-anchor="end"
      font-family="ui-monospace,...">CATEGORIA</text>
```

### Seção de legenda (sempre presente, y = status_bar + 12)
```xml
<rect x="20" y="706" width="1760" height="78" rx="6" fill="#0d1117" stroke="#1f2937" stroke-width="1"/>
<text x="38" y="724" font-size="9.5" fill="#4b5563"
      font-family="ui-monospace,...">LEGENDA</text>
<line x1="30" y1="728" x2="1770" y2="728" stroke="#1f2937" stroke-width="1"/>
<!-- swatches: rect 10x10 + text -->
<rect x="38" y="736" width="10" height="10" rx="2" fill="NODE_FILL" stroke="ACCENT" stroke-width="1.5"/>
<text x="55" y="746" font-size="9.5" fill="#8b96a8">Descrição do elemento</text>
<!-- glossário na segunda linha -->
<text x="38" y="772" font-size="9.5" fill="#4b5563">SIGLA = definição · SIGLA = definição · ...</text>
```

---

## 6. Tipografia

| Elemento | font-size | font-weight | Cor |
|----------|-----------|-------------|-----|
| Título do header | 15 | 700 | `#e6edf3` |
| Subtítulo / label de seção | 10–11 | 700 | cor do accent |
| Texto de nó / card | 9–10 | 400–700 | `#8b96a8` / `#e6edf3` |
| Código inline | 8.5–9.5 | 400 | `#2dd4bf` / `#4ade80` / `#ef4444` |
| Texto auxiliar | 8–9 | 400 | `#4b5563` |
| Monospace (cmds, paths) | igual acima | — | `font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"` |

Linha separadora entre seções: `<line stroke="#1f2937" stroke-width="1"/>` ou `stroke-dasharray="2 2"` para separadores internos.

---

## 7. Nós/cards — padrão

```xml
<!-- Card de agente -->
<rect x="X" y="Y" width="W" height="H" rx="6"
      fill="#0d1a2e" stroke="#3b82f6" stroke-width="1"/>
<text x="X+W/2" y="Y+18" font-size="9" fill="#3b82f6"
      text-anchor="middle" font-weight="700">nome-agent</text>
<text x="X+W/2" y="Y+32" font-size="8" fill="#4b5563"
      text-anchor="middle">descrição curta</text>
```

Para nó **ativo** (pulsing): adicione `<animate attributeName="stroke-opacity" .../>` dentro do `<rect>`.

Para nó com **código/snippet**:
```xml
<rect x="X" y="Y" width="W" height="H" rx="4" fill="#060c14" stroke="#1f2937" stroke-width="1"/>
<text font-family="ui-monospace,..." font-size="8.5" fill="#2dd4bf">$ comando</text>
```

---

## 8. Conexões entre nós

- **Linha simples:** `<line x1 y1 x2 y2 stroke="COLOR" stroke-width="1.5" marker-end="url(#arr-COLOR)"/>`
- **Linha tracejada (opcional/retorno):** adicione `stroke-dasharray="4 3"`
- **Curva (path):** `<path d="M x1,y1 C cx1,cy1 cx2,cy2 x2,y2" stroke="COLOR" stroke-width="1.5" fill="none" marker-end="url(#arr-COLOR)"/>`
- **Cor da linha = cor do destino** (ex: linha indo para nó verde = stroke `#4ade80`)

---

## 9. Painéis de informação densa

Para tabelas, listas de specs, checklists dentro do SVG:

```xml
<rect x="X" y="Y" width="W" height="H" rx="6"
      fill="#0d1117" stroke="#1f2937" stroke-width="1"/>
<text x="X+18" y="Y+18" font-size="10" fill="ACCENT"
      font-weight="700" font-family="ui-monospace,...">TÍTULO DO PAINEL</text>
<line x1="X+10" y1="Y+24" x2="X+W-10" y2="Y+24" stroke="#1f2937" stroke-width="1"/>
<!-- linhas de conteúdo espaçadas 14–16px -->
<text x="X+18" y="Y+40" font-size="8.5" fill="#4b5563">· item um</text>
<text x="X+18" y="Y+56" font-size="8.5" fill="#4b5563">· item dois</text>
```

Espaçamento vertical entre linhas de texto: **14–16px** para font-size 8–9, **18–20px** para font-size 10–11.

---

## 10. Saída

Salve o diagrama como arquivo `.html` autocontido, com nome `svg-NN-nome.html` (ou `nome-do-fluxo.html` quando não faz parte de uma série), na pasta de diagramas do projeto (por exemplo `assets/` ou `docs/diagrams/`). O arquivo abre direto no navegador, sem servidor e sem dependências.

O `<title>` do HTML é o nome do diagrama. Se o ambiente tiver uma ferramenta de publicação de páginas (por exemplo o Artifact do Claude Code) e o usuário pedir para compartilhar, publique o mesmo arquivo com ela; isso é opcional e não faz parte do contrato da skill.

---

## 11. Checklist antes de publicar

- [ ] `viewBox` declarado no `<svg>`
- [ ] `<defs>` com todos os markers de seta usados
- [ ] Header com accent bar na cor correta do grupo
- [ ] Status bar com dot pulsante
- [ ] Legenda com swatches e glossário
- [ ] Fade-in sequencial nos grupos principais
- [ ] Ao menos um dot animado em caminho ou timeline
- [ ] Ao menos um nó com borda pulsante (teal ou amber) indicando o elemento ativo
- [ ] Nenhuma dependência externa (JS, CSS, fontes remotas)
- [ ] Conteúdo didático e descritivo: labels explicativos, não só ícones

---

## 12. Gráficos animados (barras, empilhado, donut)

Para dados numéricos (linguagens por repositório, cobertura por módulo, custo por camada, etc.) use o gerador em vez de desenhar à mão: `scripts/chart.py` (só biblioteca padrão do Python). Ele aceita **qualquer quantidade de itens**, valores, porcentagens e cores; nada é fixo.

```sh
python scripts/chart.py dados.json saida.svg [--type stacked|bars|donut] [--html]
```

| Tipo | Visual | Quando usar |
|------|--------|-------------|
| `stacked` | Uma barra arredondada dividida em segmentos proporcionais, com legenda em duas colunas (`● nome: 48.30%`), no estilo "top linguagens" | Composição de um total; poucos a muitos itens |
| `bars` | Uma barra por item, com trilho, cada uma em sua porcentagem | Comparar itens independentes (cobertura, progresso, notas) |
| `donut` | Anel com arcos proporcionais e legenda ao lado | Composição com ênfase visual |

Campos do JSON (veja `examples/`):

- `title`, `type`, `width` (padrão 400, 480 ou 460 conforme o tipo), `bg` (`"transparent"` ou cor; padrão `#0b0f17`), `text` e `title_color` (cores de texto).
- `items[]`: `label`, `value`, `color` opcional (sem cor, cicla a paleta do design system: azul, teal, âmbar, verde, violeta, rosa, vermelho). Use as cores de grupo da seção 2 para dar significado (vermelho = crítico, verde = ok).
- `mode`: `"share"` (padrão) calcula `valor / soma` e mostra porcentagem com 2 casas, então os valores não precisam somar 100; `"absolute"` desenha cada barra proporcional a `max` (padrão 100) e mostra o valor com `unit` (por exemplo `%`, `ms`, `R$`).

Animações geradas (SMIL, sem JS): segmentos e barras crescem da esquerda com entrada escalonada, arcos do donut se desenham em sequência, legendas e valores aparecem em fade-in.

Regras:

- Passe `--html` quando o gráfico for aberto sozinho; sem a flag, o `.svg` puro serve para embutir em README ou páginas (use `bg: "transparent"` para fundo claro ou escuro).
- Se o tipo de gráfico não existir no gerador (linhas, barras verticais, dispersão), escreva o SVG à mão com os mesmos padrões: `<animate attributeName="width|height|stroke-dasharray" to=... fill="freeze"/>` com `begin` escalonado, cores da seção 2 e tipografia da seção 6. Gráficos dentro de um diagrama maior (seções 1 a 9) também são desenhados à mão.
- Rótulos longos: aumente `width` em vez de reduzir a fonte.
- Verifique o resultado abrindo no navegador (ou `python -c "import xml.dom.minidom as m; m.parse('saida.svg')"` para validar o XML).

---

## 13. Banner de título de projeto (hero)

Para o topo de um README ou página de projeto: título, subtítulo, pills da stack e, à direita, um **painel criativo animado** que representa o projeto. Use `scripts/hero.py`:

```sh
python scripts/hero.py projeto.json hero.svg [--html]
```

Tamanho padrão 1200×300 (cresce sozinho se as pills quebrarem de linha). Modelo de referência: título com barra em gradiente, subtítulo revelado da esquerda, pills da stack em fade-in e painel à direita.

### Campos do JSON (veja `examples/hero-*.json`)

- `title`: nome do projeto (a fonte encolhe sozinha se for longo).
- `tagline`: lista de trechos; texto simples fica discreto, `{"text": "...", "accent": true}` ganha a cor de destaque. Diga o que o projeto **faz** e o diferencial, não só a tecnologia.
- `stack`: lista de pills; cada item é texto ou `{"label": "Redis", "color": "#ef4444"}` (cor de marca da tecnologia, com ponto e borda coloridos).
- `palette`: sobrescreve qualquer token (`bg`, `surface`, `border`, `text`, `muted`, `dim`, `accent`, `accent2`, `ok`, `warn`, `err`). O que faltar usa o design system.
- `panel`: `{"type": ..., "title": ..., "width": 336, ...}` ou `null` para um banner só de texto.

### Escolha o painel pelo projeto

O painel deve contar a história do projeto. Escolha pelo que o projeto **é**, não pelo que é mais fácil:

| `type` | Dados | Quando usar |
|--------|-------|-------------|
| `terminal` | `lines`: `{"cmd"}`, `{"out"}`, `{"ok"}`, `{"warn"}`, `{"err"}` | DevOps, CI/CD, containers, CLI, infraestrutura. Use os **comandos reais** da stack (docker, kubectl, terraform, helm, gh, aws, npm...) |
| `editor` | `lines`: texto ou trechos `["texto", "kw\|fn\|str\|num\|com\|err"]` | Bibliotecas, SDKs, APIs, projeto centrado numa linguagem: mostre um trecho idiomático e curto dela (decorators em Python, `async/await`, handlers, queries) |
| `pipeline` | `stages`: `{"label", "status": ok\|run\|fail\|pending, "detail"}` | Entrega contínua, ETL, jobs, filas, fluxo de aprovação |
| `metrics` | `kpis` (até 3: `value`, `label`, `color`) e `series` (barras) | Fintech, analytics, e-commerce, saúde operacional, qualquer produto cujo valor é número |
| `architecture` | `nodes` (`label`, `color`, `active`) e `edges` (pares de índices) | Serverless, microsserviços, integrações, provedores de nuvem e serviços externos |
| `custom` | `svg`: fragmento SVG desenhado à mão, coordenadas locais (0,0 = canto do painel) | Nichos que nenhum painel acima representa: mapa, jogo, áudio, mobile, IoT, dados científicos. Use as animações da seção 3 |

Varie de projeto para projeto: não use terminal em tudo. Combine sinais: a linguagem principal (qual trecho de código), o nicho (que métricas ou que fluxo faria sentido), os serviços e provedores (quais nós e quais comandos), a fase (pipeline passando, deploy em andamento). Conteúdo plausível e específico (nomes de serviço, rotas, versões, tempos) vale mais que genérico, mas **nunca invente números como se fossem dados reais**: nos exemplos e em banners decorativos, mantenha valores claramente ilustrativos e, se forem métricas verdadeiras, extraia-as do projeto.

### Paleta do projeto

Antes de escolher cores, procure a paleta que o projeto já tem e use-a em `palette` (normalmente `accent`, `accent2` e, se o projeto for escuro ou tiver fundo próprio, `bg`, `surface`, `border`):

1. Tokens de design: `tailwind.config.*` (`theme.extend.colors`), `theme.ts`/`tokens.json`, variáveis CSS (`:root { --primary }`), Material/Flutter `ThemeData`, `colors.xml`, `Assets.xcassets`.
2. Identidade: `manifest.json` (`theme_color`, `background_color`), logo e favicon (cores dominantes), `README` e badges, site oficial.
3. Marca da stack, quando não há paleta própria: cor oficial de cada tecnologia para as pills (Docker `#2496ed`, Python `#3776ab`, Node `#5fa04e`, Postgres `#336791`...).
4. Sem nada disso, mantenha a paleta padrão do design system (teal e azul).

Use no máximo duas cores de destaque. Verifique contraste do `accent` sobre o `bg` e do texto sobre `surface`; fundo claro de marca exige também trocar `text`, `muted`, `border` e `surface`. Registre de onde a paleta veio (arquivo ou URL) ao entregar.

### Fluxo

1. Leia o projeto (README, manifestos, `Dockerfile`, workflows de CI, IaC, dependências) para obter nome, propósito, stack, serviços e provedores reais.
2. Defina paleta e tipo de painel pelas regras acima e escreva o JSON.
3. Gere, abra no navegador (ou renderize) e confira: texto cortado, painel transbordando (o gerador avisa quando há linhas demais), contraste e pills.
4. Salve o `.svg` onde o README do projeto possa referenciá-lo (`![](assets/hero.svg)`).
