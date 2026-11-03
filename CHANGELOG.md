# <img src="assets/icons/teal/file-text.svg" width="28" align="top"> Changelog

<p align="center">
  <img src="https://img.shields.io/badge/versão_atual-1.3.0-0ea5a4?style=flat-square" alt="Versão atual 1.3.0">
  <img src="https://img.shields.io/badge/formato-Keep_a_Changelog-8b96a8?style=flat-square" alt="Formato Keep a Changelog">
  <img src="https://img.shields.io/badge/versionamento-template.json-60a5fa?style=flat-square" alt="Versões seguem template.json">
</p>

Formato baseado em Keep a Changelog. Versões seguem `template.json`.

[← Voltar ao README](README.md#sumario) · [Compatibilidade](docs/compatibility.md) · [Validação](docs/validation.md)

| Versão | Data | Destaque |
|---|---|---|
| [Não lançado](#não-lançado) | n/d | Instalação de mods (`--mod`), mod `token-handoff`, skills `dark-pipeline-svg` e `readme-styling`, guia dos diagramas, README estilizado com sumário |
| [1.3.0](#130---2026-10-29) | 2026-10-29 | Instalador de um comando e README explicado |
| [1.2.0](#120---2026-10-29) | 2026-10-29 | Economia, continuidade de sessão e comunicação |
| [1.1.0](#110---2026-10-19) | 2026-10-19 | Generalização, 28 papéis e gestão de produto |
| [1.0.0](#100) | n/d | Template portátil com 18 especialistas |

## [Não lançado]

### Adicionado
- **Instalação de mods (`install.py --mod <nome> [--mod-scope project|global]`):** `integrations/mod/` guarda
  mods do Claude Code; `scripts/mods.py` copia o mod e seus scripts para `.claude/` do projeto ou do usuário, registra
  um marketplace local, instala o plugin pelo `claude plugin` e acrescenta a linha em
  `docs/operations/registro-instalacoes.md`. Aceita `--dry-run`. Os mods ficam fora de `.engineering/`.
- **Mod `token-handoff`:** só o marco de 400k (sem marcos de 100k/200k/300k e sem perguntas ao humano). Aos 400k
  bloqueia novos agentes, faz o modelo gravar o prompt de continuação e, com o arquivo pronto e sem agente ativo,
  abre a sessão nova com ele e encerra a atual. Windows apenas; testado por unidade, não verificado em sessão real.
- **Skill `dark-pipeline-svg`:** gera diagramas SVG animados (SMIL) em HTML autocontido no
  design system dark pipeline: paleta por grupo, cabeçalho, barra de status e legenda. Registrada
  em `template.json` e instalada em `.claude/skills` e `.agents/skills`.
  Inclui `scripts/chart.py` (gráficos animados `stacked`, `bars` e `donut` a partir de JSON, itens,
  porcentagens e cores livres) e `scripts/hero.py` (banner de título de projeto com stack e painel animado: `terminal`, `editor`,
  `pipeline`, `metrics`, `architecture` ou `custom`, com paleta do projeto); exemplos em `examples/`.
- **Skill `readme-styling`:** escreve README e markdowns estilizados (banner SVG animado, badges, grids,
  código com coloração, diagramas e gráficos via `dark-pipeline-svg`) com `scripts/lucide_icon.py`
  para recolorir ícones, `scripts/code_card.py` (cartões de código e de árvore em SVG com realce por linguagem) e
  `scripts/table_card.py` (cartões de tabela a partir de markdown), sempre acompanhados do texto copiável, e `templates/README.template.md` (modelo de README).
- **`docs/diagramas.md`:** guia aprofundado dos 18 diagramas (macro e micro), cada um exibido na própria
  página em SVG animado (`assets/diagramas/`, extraído dos HTML): fluxo de implementação,
  regras dos agentes com link para o arquivo de origem e, em cada etapa, o que é só ilustração do
  desenho e diverge do contrato real (por exemplo estados do quadro, tentativas de correção, DoD).
- **`assets/icons/`:** biblioteca Lucide completa (2275 SVGs, ISC) e conjunto padrão por assunto.
- **`assets/`:** galeria de 17 diagramas do passo a passo do template, mais o fluxo macro e um
  exemplo avulso de fluxo de embedding, com índice em planilha.

- **Quadro vivo (regra):** prazos de frescor, dois donos que atestam cada card (demanda e entrega),
  conferência independente do principal e revisão do quadro a cada handoff, diário ou estado vivo gravado.
  Em `core/workflow/github-projects.md`, `economy.md` e `session-continuity.md`.
- **Varredura de segredos sem ler o valor (regra):** a busca usa só lista de arquivos ou contagem
  (`files_with_matches`/`count`, `rg -l`/`-c`), nunca saída de conteúdo; confirmar um achado exige
  mascarar o valor ou autorização explícita para o arquivo. Em `core/policies/safety.md`.
- **Política `versioning`:** toda mudança que entra na `main` recebe antes uma tag SemVer, publicada
  antes do código, pelo principal; não concede autorização de push (`core/policies/versioning.md`).

### Alterado
- **README:** refeito com a skill `readme-styling` (banner, badges, grids, gráficos, cartões de código); nova seção sobre os diagramas, skills atualizadas (três) e estrutura com `assets/`. Ganhou um **Sumário** no início, com redirecionamento para as seções e para os documentos de `docs/`, e as tabelas do glossário (ações, políticas, fluxos e integrações) passaram a cartões SVG com o texto copiável em `<details>`.
- **`docs/compatibility.md`, `docs/validation.md` e este changelog:** estilizados no mesmo padrão (cabeçalhos com ícone, badges, tabelas e destaques), com links de volta ao Sumário do README. Todas as tabelas de conteúdo de `docs/` viraram cartões SVG (`assets/tabelas/`) com o texto copiável em `<details>`; só as tabelas de navegação, em que o link é o ponto, ficam em markdown.
- **Documentação:** contagens e menções de skills nos adapters e em `docs/` alinhadas com o catálogo (11 ações, 3 skills, 18 diagramas).

### Corrigido
- `assets/svg-03-brainstorm.html`: tag `</brief>` perdida dentro de um `<text>`, que invalidava o SVG fora do navegador.

## [1.3.0] - 2026-10-29

### Adicionado
- **`install.py`:** instalador de um comando (`python install.py <projeto>`). Instala ou, se o
  projeto já tem o template, atualiza reaproveitando perfis, provedores e tiers anteriores;
  aceita `--profiles`, `--providers`, `--tier` e `--dry-run`, roda `check` ao final e recusa o
  próprio template como destino. Padrão: `base,product-team,github-projects` para claude e codex.
- **README:** comandos explicados (instalador e CLI), perfis em linguagem simples, como instalar
  todos os perfis compatíveis (`hosting-managed` e `vps-k3s` são excludentes), estrutura do projeto
  comentada e glossário (ações, papéis, skills, políticas, workflows, templates, integrações).

## [1.2.0] - 2026-10-29

Práticas operacionais evoluídas em uso real, generalizadas (sem nomes de projeto). Base: `main` 1.1.0.

### Adicionado
- **Workflows:** `economy.md` (modo econômico: um autor por vez, brief por referência, handoff em
  arquivo, não retomar agente pesado, escopo antes de suíte, gates uma vez por snapshot;
  muda como se executa, nunca se verifica, nenhum gate removido) e `session-continuity.md`
  (marcos de tokens configuráveis, padrão 100k/200k/300k perguntam e 400k obriga a encerrar;
  diário de eventos só de acréscimo; estado vivo de até 25 linhas com gravação atômica;
  retomada após queda sem retomar agente perdido).
- **Política:** `communication.md` (IDs com link para arquivo e linha, nome por extenso,
  frase em linguagem simples, perguntas sempre com recomendação).
- **Templates (total 20):** `diary`, `live-state`, `continuation-prompt`.
- **Perfil `session-continuity` (opt-in; total 10):** ativa a continuidade de sessão. Economia
  e comunicação ficam no core por não removerem gate nem interromperem o usuário.
- **`integrations/token-milestones/README.md`:** especificação do contador automático e do
  diário; sem código.
- Testes: arquivos novos no render, perfil válido, `check`, neutralidade dos arquivos novos.

### Alterado
- `templates/brief.md`: campo de referências; `templates/handoff.md`: limite de 40 linhas.
- `scripts/template.py`: uma frase em `COMMON` apontando para os novos contratos; sem mudança
  de comportamento.
- `README.md`, `core/catalog.md`, `docs/compatibility.md`, `docs/validation.md`.

### Não verificado
- Nenhum agente real foi observado seguindo economia, marcos ou retomada; o mecanismo
  automático de marcos é só especificação e não foi validado em runtime.

## [1.1.0] - 2026-10-19

Generalização do template (sem nomes de projeto no core) e inclusão de gestão de produto.
Base: tag `v1.0.0` (commit `81ee341`).

### Adicionado
- **Papéis (10 novos, total 28):** product-owner, ux-researcher, ux-designer, ui-designer,
  brand-strategist, marketing, frontend-senior, privacy-compliance, lay-user, scribe.
  Novo modo `author` (sem shell) para papéis que produzem artefatos.
- **Ações:** `/story`, `/privacy`, `/usability` (total 11).
- **Perfis:** `product-team` e `polyrepo` (total 9).
- **Políticas:** `models.md` (camadas deep/standard/light), `installations.md`
  (registro obrigatório de toda instalação), `quality-principles.md` (reuso, idempotência,
  tolerância a falhas, escalabilidade, simplicidade, verificabilidade).
- **Workflows:** `staffing.md`, `user-stories.md` (DoR/DoD), `usability.md`
  (dois usuários leigos simulados + brainstorm de decisão), `polyrepo.md` (hub + repositórios).
- **Templates:** `decision`, `persona`, `registro-instalacoes`, `staffing`,
  `usability-report`, `user-story`.
- **Camadas de modelo por papel:** `model_tiers` e `roles[].tier` em `template.json`;
  adapter Claude grava `model:` no cabeçalho do agente, Codex grava `model_reasoning_effort`.
  Override por projeto via `--tier ROLE=TIER`, registrado em `project.json` e no manifesto.
  Papéis de gate (qa, security, reviewer, privacy-compliance) não podem ficar abaixo de `standard`.
- **`integrations/plugins/`:** curadoria (`curated.json`, README) de plugins/agentes externos;
  o template não instala nada.
- **GitHub Projects:** campos `Type` (epic/story/task/bug/spike) e `Estimate`; labels
  `type:*`, `tier:*` e `role:*` dos novos papéis.
- Validação: papéis base obrigatórios, camadas válidas, rejeição de override inválido.
- Testes ampliados (`tests/test_template.py`): 26 testes, 1 ignorado.
- Este `CHANGELOG.md`.

### Alterado
- `architect`, `backend`, `security`: texto específico de stack (NestJS/MikroORM/AWS) passou
  a ser condicionado ao perfil selecionado; o core não cita projeto nem stack fixa.
- `workflow/engineering.md`: fluxo começa em história com DoR; seção de deveres de gestão
  do principal; gates incluem conformidade de design, privacidade e rodada de usabilidade.
- `workflow/github-projects.md`: títulos `[S-NNN]`/`[E-NN]`, histórias como sub-issues de
  épicos, tarefas como sub-issues de histórias.
- `templates/brief.md`: campos `Model tier` e `Staffing plan`.
- `policies/integrations.md`: modelos agora seguem camadas lógicas, não mais "herdar".
- `scripts/template.py`: `install` aceita a pasta-raiz do workspace que contém o checkout do
  template (rejeita só sobrescrita de arquivos do próprio template); `retired_paths`
  permite ao `sync` aposentar arquivos antigos; manifesto passa a guardar `tiers`.
- `README.md`, `core/catalog.md`, `docs/compatibility.md`, `docs/validation.md`,
  `integrations/voltagent/README.md`, `integrations/github-projects/*`: atualizados para
  28 papéis, 11 ações, 9 perfis e as novas regras.

### Removido
- Premissa de que adapters Codex omitem `model`; o limite fixo de exatamente 18 papéis e 8 ações.

### Não verificado
- Efeito dos campos `model`/`model_reasoning_effort` gerados em runtime real, execução paralela
  de dois usuários leigos e rodada de usabilidade completa (ver `docs/validation.md`).
  Popularidade em `curated.json` foi lida na data de curadoria.

## [1.0.0]

Estado da `main` em `81ee341` (tag `v1.0.0`): template portátil com 18 especialistas,
8 ações, 7 perfis, adapters Claude/Codex e workflow com GitHub Projects no lugar do
Kanban Markdown.
