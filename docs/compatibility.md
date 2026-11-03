# <img src="../assets/icons/teal/plug.svg" width="28" align="top"> Compatibilidade e evidências

<p align="center">
  <img src="https://img.shields.io/badge/consulta_documental-2026--10--08-0ea5a4?style=flat-square" alt="Consulta documental em 2026-10-08">
  <img src="https://img.shields.io/badge/Codex-0.156.1-000000?style=flat-square" alt="Codex 0.156.1">
  <img src="https://img.shields.io/badge/Claude_Code-2.1.294-D97757?style=flat-square" alt="Claude Code 2.1.294">
  <img src="https://img.shields.io/badge/runtime-não_validado-f59e0b?style=flat-square" alt="Runtime não totalmente validado">
</p>

> [!NOTE]
> As versões acima são contexto de compatibilidade informado na preparação; **não representam uma matriz de runtime integralmente validada.**

[← Voltar ao README](../README.md#sumario) · [Comando guilda](cli.md) · [Validação](validation.md) · [Guia dos diagramas](diagramas.md)

## Sumário

| Seção | O que cobre |
|---|---|
| [Codex](#codex) | Agentes em TOML, esforço de raciocínio e skills em `.agents/skills` |
| [Claude Code](#claude-code) | Agentes do projeto, plugin e limites de paridade |
| [Modelos por papel](#modelos-por-papel) | Campo `model` por camada e o que ele não prova |
| [Marcos de tokens](#marcos-de-tokens-120) | Especificação sem código validado |
| [Pacote guilda](#pacote-guilda-200) | Python, sistemas, distribuição (wheel, sdist, CI e release) e o que o pacote 2.0.0 não comprova |
| [Integrações e escopo](#integrações-e-escopo-da-verificação) | Serena, RTK, Superpowers, Voltagent e GitHub Projects |

---

<a id="codex"></a>

## <img src="../assets/icons/teal/terminal.svg" width="24" align="top"> Codex

[Configuração de subagentes](https://learn.chatgpt.com/docs/agent-configuration/subagents) descreve arquivos TOML em `.codex/agents` com `name`, `description` e `developer_instructions`.

- O adapter emite `model_reasoning_effort` por papel a partir da camada (`deep`=high, `standard`=medium, `light`=low) e omite `model` para herdar o modelo da sessão.
- O nome do campo e seu efeito dependem da versão do Codex e **não foram verificados em execução**.
- `agents.enabled` é habilitado por padrão segundo essa documentação, mas políticas de sessão ou do processo principal podem restringir delegação e acesso. Um campo de configuração não supera o runtime.

[Skills](https://learn.chatgpt.com/docs/build-skills) documenta `.agents/skills` para skills do projeto. O adapter materializa nesse caminho as skills do catálogo (`drawio-diagram`, `dark-pipeline-svg` e `readme-styling`) e as ações. Descoberta e invocação precisam ser verificadas na sessão de destino.

<a id="claude-code"></a>

## <img src="../assets/icons/teal/bot.svg" width="24" align="top"> Claude Code

[Subagentes](https://code.claude.com/docs/en/sub-agents) documenta agentes do projeto em `.claude/agents`. [Referência de plugins](https://code.claude.com/docs/en/plugins-reference) descreve os componentes agents, commands, skills e o manifesto `.claude-plugin`. O pacote referencia arquivos de agentes explicitamente no manifesto.

> [!WARNING]
> As capacidades de um agente de plugin diferem das de agentes de projeto: `permissionMode`, `hooks` e `mcpServers` de agentes de plugin são **ignorados** conforme a documentação consultada. Por isso a paridade abrange instruções e catálogo; não promete equivalência de sandbox, permissões ou ferramentas. As integrações MCP permanecem configuração separada do projeto.

**Consumo do plugin.** Exige também disponibilizar seus contratos COMMON em `.engineering` na raiz do consumidor e mesclar `BOOTSTRAP.md` em `CLAUDE.md`. A [receita do adapter](../adapters/claude/README.md) copia a árvore compartilhada sem `manifest.json` e aborta se `.engineering` já existir.

- É exportação para leitura, sem manifesto de instalação gerenciada: `check` e `sync` só se aplicam à raiz do pacote plugin nesse fluxo.
- Os agentes nativos permanecem no plugin.
- Presença de contratos e resolução de caminhos numa fixture não comprovam descoberta nativa nem habilitação automática.

<a id="modelos-por-papel"></a>

## <img src="../assets/icons/teal/gauge.svg" width="24" align="top"> Modelos por papel

<img alt="Tabela Modelos por papel: colunas Provedor, O que o adapter escreve, Origem" src="../assets/tabelas/compatibility-01-modelos-por-papel.svg" width="100%">

<details>
<summary>Ver como texto</summary>

| Provedor | O que o adapter escreve | Origem |
|---|---|---|
| Claude Code | `model: opus`, `sonnet` ou `haiku` no cabeçalho de cada agente | Camada do papel em `template.json` (`model_tiers`) |
| Codex | `model_reasoning_effort` (high, medium, low) | Mesma camada; `model` omitido |

</details>

O principal pode sobrescrever o modelo por despacho. Nos agentes de plugin o campo `model` é lido do cabeçalho do agente; a documentação consultada deve ser rechecada na versão instalada.

> [!WARNING]
> Um campo gerado nunca prova que o runtime o honrou: confirme com uma sessão real antes de depender dele para custo ou qualidade. Camadas e nomes de modelo mudam com o catálogo do provedor; atualize `model_tiers` em um único lugar.

<a id="marcos-de-tokens-120"></a>

## <img src="../assets/icons/teal/package.svg" width="24" align="top"> Marcos de tokens (1.2.0)

[integrations/token-milestones/README.md](../integrations/token-milestones/README.md) é uma **especificação**. O template não traz código nem foi validado contra um runtime: o contador de uso da sessão, o bloqueio de despachos e o evento de fim de subagente variam por provedor e versão e precisam ser confirmados na instalação de destino. Sem o mecanismo automático, [session-continuity.md](../core/workflow/session-continuity.md) vale por estimativa do agente.

<a id="pacote-guilda-200"></a>

## <img src="../assets/icons/teal/package.svg" width="24" align="top"> Pacote guilda (2.0.0)

- **Requisitos:** Python 3.11 ou superior, só biblioteca padrão (o `pyproject.toml` não declara dependências). Instalação por `pip install guilda` ou `uv tool install guilda`; a partir do checkout, `install.py` e `scripts/template.py` são atalhos finos para o mesmo código. Comandos e limitações em [cli.md](cli.md).
- **Sistemas:** a CI roda em Linux e Windows, com Python 3.11, 3.12 e 3.13. macOS e Python 3.14 não estão na matriz. O mod `token-handoff` só instala no Windows.
- **Contrato com projetos instalados:** o manifesto passa a se chamar `guilda`; projetos antigos migram com `guilda upgrade --dry-run` e depois `guilda upgrade`, inclusive instalações 1.3.0 feitas de um checkout com `core/graphify-out/`. Mods novos usam o marketplace `guilda-mods`.
- **Comandos que dependem de terceiros:** `promote` exige o `gh` autenticado, `self-update` roda `pip` ou `uv` e `mod` roda `claude plugin`. Nos testes esses comandos usam executores simulados; **nenhuma issue, gist, atualização ou instalação de plugin real foi feita** nessa verificação.
- **Verificação automática de versão:** opcional e desligada por padrão (`guilda config set update-check off|notify|auto`). É o único aviso de versão nova: o `upgrade` não consulta o PyPI e, com a verificação desligada, atualiza o projeto para o template da versão instalada sem avisar que existe outra.

<a id="distribuicao"></a>

### Distribuição e publicação

- **Wheel:** leva o pacote `guilda/` (código e `payload.txt`) e, em `guilda/_data/`, só os arquivos listados em `guilda/payload.txt` (hoje 138, entre eles `template.json`). O hook `hatch_build.py` faz essa inclusão. `install.py`, `scripts/`, `docs/`, `assets/`, `tests/` e `.github/` não entram no wheel.
- **Allowlist:** `payload.txt` é gerado a partir dos arquivos versionados em `core/`, `profiles/`, `adapters/`, `integrations/` e `template.json` (`python -m guilda.payload --write`) e conferido por `python -m guilda.payload --check`. Caminhos com segmentos internos (`graphify-out`, `docs/superpowers`, `plans`, `specs`, `.worktrees`, `.dev`, `__pycache__`) são recusados. No uso, o motor só lê arquivos da lista; arquivo solto na pasta (por exemplo uma saída de ferramenta não versionada) é ignorado.
- **sdist:** o `pyproject.toml` não filtra o sdist, então ele segue o padrão do hatchling (os arquivos do projeto, menos o que o `.gitignore` exclui). `scripts/check_dist.py` recusa material interno no sdist e confere no wheel o `template.json`, o `core/`, a licença em `*.dist-info/licenses/` e a ausência de `docs/`, `assets/`, `tests/` e `.github/`.
- **CI (`ci.yml`):** em pull request para `develop` ou `main` e em push de `feature/**` e `release/**`: a suíte na matriz Linux e Windows × Python 3.11 a 3.13; a conferência do payload e a busca de material interno versionado; e a construção do sdist e do wheel com `python -m build`, seguida de `tests.test_guilda_wheel`.
- **Release (`release.yml`):** disparado por tag `v*`. `verify` (matriz completa) confere que a tag bate com `template.json` e `guilda/__version__.py` (`scripts/check_release.py`), que o commit da tag já está na `main`, o payload e a suíte; `build` gera e inspeciona `dist/`; `publish` roda no ambiente `pypi` do GitHub, que exige aprovação manual do mantenedor, e publica por *trusted publishing* (OIDC, sem token guardado). Todas as actions estão fixadas por SHA.
- **Versão:** `template.json` e `guilda/__version__.py` têm de coincidir (teste e `check_release.py`). A política de versionamento do template ([versioning.md](../core/policies/versioning.md)) pede a tag SemVer antes do código na `main`; o fluxo de release, por sua vez, exige que o commit da tag já esteja na `main` antes de publicar.

<a id="integrações-e-escopo-da-verificação"></a>

## <img src="../assets/icons/teal/shield-check.svg" width="24" align="top"> Integrações e escopo da verificação

<img alt="Tabela Integrações e escopo da verificação: colunas Integração, Situação" src="../assets/tabelas/compatibility-02-integracoes-e-escopo-da-verificacao.svg" width="100%">

<details>
<summary>Ver como texto</summary>

| Integração | Situação |
|---|---|
| Serena | Presença local do executável e opções `start-mcp-server`, `--project-from-cwd` e `--context` confirmadas pelo help da CLI em 2026-10-08. O contexto `ide-assistant` e a conexão MCP devem ser confirmados na instalação de destino. O arquivo de projeto deriva de `.serena/project.yml` sanitizado, sem nome ou memórias do projeto de origem. |
| RTK | Orientação derivada de `RTK.md` local; não há interceptador Codex incluído. |
| Superpowers | Dependência opcional documentada, sem código copiado. |
| Voltagent | Os oito pacotes derivam da configuração local e permanecem `configured_not_verified`. |
| GitHub Projects | Os scripts de `integrations/github-projects` criam o Project com os nove estados do contrato e os campos e labels padrão. O Kanban Markdown do VS Code foi descontinuado e os cards antigos têm mapeamento explícito de importação. |

</details>

> [!WARNING]
> Arquivos e validação estática **não comprovam** instalação de plugins, conexão de MCP, descoberta de agentes ou skills, revisão independente, renderização do board ou deploy. Testes de descoberta e paridade funcional em sessões novas de ambos os provedores permanecem pendentes. Não use a expressão "runtime totalmente verificado" até haver evidência dessas execuções.
