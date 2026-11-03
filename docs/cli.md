# <img src="../assets/icons/teal/terminal.svg" width="28" align="top"> Referência do comando `guilda`

Como a versão 2.0.0 se comporta, comando por comando. Tudo aqui foi conferido no código (`guilda/`) e nos testes (`tests/`); onde algo não foi verificado, o texto diz.

[← Voltar ao README](../README.md#sumario) · [Compatibilidade](compatibility.md) · [Validação](validation.md)

## Sumário

| Seção | O que cobre |
|---|---|
| [Instalar o comando](#instalar) | `pip`/`uv`, o que vem no pacote, o que **não** é instalado |
| [Comandos do motor](#motor) | `init`, `sync`, `check`, `doctor`, `package` |
| [`install`](#install) | Instalar ou atualizar com padrões |
| [`upgrade`](#upgrade) | Atualização arquivo por arquivo, conflitos, rollback e migração da 1.3.0 |
| [Arquivo mantido e `check`](#arquivo-mantido) | Limitação conhecida e como resolver |
| [`promote`](#promote) | Propor alterações locais (gist secreto + issue) |
| [`self-update` e `config`](#self-update) | Atualizar o próprio `guilda` e a verificação de versão |
| [`mod`](#mod) | Mods do Claude Code |
| [Códigos de saída](#saida) | 0, 1 e 2 |

<a id="instalar"></a>

## Instalar o comando

```sh
pip install guilda
# ou
uv tool install guilda

guilda --help            # ou: python -m guilda --help
```

- Requer Python 3.11 ou superior. O pacote não tem dependências: só a biblioteca padrão.
- O template (papéis, ações, políticas, perfis, integrações) vai **dentro do pacote**, em `guilda/_data/`. Não é preciso clonar o repositório: o `guilda` funciona em qualquer pasta, e o projeto de destino é um argumento (`install`, `upgrade`, `promote`) ou `--target` (`init`, `sync`, `check`, `package`, `mod`).
- `install` e `init` só gravam dentro da pasta do projeto: `.engineering/`, `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.codex/` e `.agents/skills/` (lista completa em [O que é gravado no projeto](../README.md#o-que-é-gravado-no-projeto)). Não instalam programas, não mudam configurações globais e não ativam integrações.
- `doctor` só diagnostica: procura `claude`, `codex`, `git`, `rtk` e `serena` no PATH e não executa nenhum deles.
- Só estes comandos vão além do projeto, e só quando você os roda ou liga: `self-update` (roda `pip` ou `uv`), `config set update-check auto` (atualiza sozinho), `mod` (copia arquivos para `.claude/` e roda `claude plugin`) e `promote` (publica no GitHub pelo `gh`). `config set` e a verificação automática gravam o arquivo de configuração do usuário.

**A partir do checkout.** Quem usa o repositório diretamente tem dois atalhos finos para o mesmo código: `python install.py ...` equivale a `guilda install ...`, e `python scripts/template.py ...` equivale a `guilda init|sync|check|doctor|package ...`. A diferença é que, no checkout, o template lido é o da própria pasta, e `scripts/template.py` não faz a verificação automática de versão.

<a id="motor"></a>

## Comandos do motor: `init`, `sync`, `check`, `doctor`, `package`

São repassados sem alteração ao motor (`guilda/engine.py`). Saída em JSON no stdout; erro como `error: <mensagem>` (em inglês) no stderr, com código 1.

| Opção | Significado |
| --- | --- |
| `--target <pasta>` | Projeto de destino. Obrigatória em `init`, `sync` e `package`; opcional em `check`. |
| `--providers claude,codex` | Para quais ferramentas gerar arquivos. Padrão: as duas. |
| `--provider claude` | Só em `package` (obrigatória nele). |
| `--profiles a,b` | Perfis. Padrão: `base` (diferente do `install`, cujo padrão tem três perfis). |
| `--tier papel=camada` | Camada de modelo de um papel; repetível. Gates (`qa`, `security`, `reviewer`, `privacy-compliance`) nunca abaixo de `standard`. |
| `--dry-run` | Faz toda a checagem e só lista o que seria gravado ou removido. |

- **`init`**: instala. Antes de gravar qualquer coisa, confere todos os caminhos; um arquivo seu com o mesmo nome e conteúdo diferente (`preexisting conflict`) aborta sem gravar nada. Saída: `{"write": [...], "remove": [...], "dry_run": ...}`.
- **`sync`**: refaz uma instalação existente (sem manifesto: `sync requires installed manifest`). Usa as opções **passadas na linha de comando**, não as registradas: sem `--profiles`, vale `base`, e os arquivos dos outros perfis são removidos; sem `--tier`, os overrides somem. Passe as mesmas opções da instalação ou use `guilda install`/`guilda upgrade`, que reaproveitam as escolhas registradas. Arquivo gerenciado editado à mão faz o comando parar com `installed drift: <arquivo>`, sem gravar nada.
- **`check`**: não grava nada. Sem `--target`, valida o template e mostra `{"valid": true, "roles": 28, "actions": 11}`. Com `--target`, confere o manifesto, o conteúdo de cada arquivo gerenciado (`installed drift`) e se o template é mais novo que a instalação (`source update available; run sync`).
- **`doctor`**: mostra a versão do Python e, para `claude`, `codex`, `git`, `rtk` e `serena`, o caminho encontrado (ou `null`) e um estado (`detected; version/discovery unverified` ou `absent`). Não executa nem instala nada.
- **`package --provider claude --target <pasta-separada>`**: gera o plugin do Claude (`agents/`, `commands/`, `skills/`, `.claude-plugin/`, `.engineering/`, `BOOTSTRAP.md`, `PLUGIN_SETUP.md`). Não instala nem habilita o plugin; veja o [adapter Claude](../adapters/claude/README.md).

Manifesto com o nome antigo (`engineering-template`, de antes da 2.0.0): `sync` e `check` recusam com `legacy manifest name; run guilda upgrade`.

<a id="install"></a>

## `guilda install [projeto]`

Instala; se o projeto já tem manifesto, atualiza. Sem `projeto`, usa a pasta atual.

| Opção | O que faz |
| --- | --- |
| `--profiles a,b` | Padrão: `base,product-team,github-projects`; numa atualização, os perfis já instalados. |
| `--providers a,b` | Padrão: `claude,codex`; numa atualização, os já instalados. |
| `--tier papel=camada` | Repetível; soma-se às camadas já registradas. |
| `--mod nome` | Instala também um [mod](#mod); repetível. |
| `--mod-scope project\|global` | Escopo do mod. Padrão: `project`. |
| `--dry-run` | Só mostra quantos arquivos seriam gravados ou removidos. |

```text
$ guilda install meu-projeto
instalação (concluída) em /caminho/meu-projeto
  perfis: base, product-team, github-projects | provedores: claude, codex
  252 arquivos gravados, 0 removidos
  verificação (check): ok
```

- Recusa um destino que seja arquivo ou que fique dentro do próprio template.
- Ao terminar, roda o `check` estrito. Numa atualização, um arquivo gerenciado editado à mão faz o comando parar com `installed drift` e a dica de mover ou reverter o arquivo; nada é gravado.
- Manifesto com o nome antigo: o comando para e pede `guilda upgrade`.
- Com `--mod`, o mod é instalado depois do template. Se o mod falhar, o código de saída é 1, mas o template já foi gravado.

<a id="upgrade"></a>

## `guilda upgrade [projeto] [--dry-run] [--yes]`

Atualiza um projeto instalado para o template da versão do `guilda` em uso, arquivo por arquivo, com os mesmos perfis, provedores e camadas registrados no manifesto (não há opção para mudá-los aqui). Não consulta o PyPI (só a verificação automática opcional, `update_check` em `notify` ou `auto`, consulta antes de qualquer comando): para ter um template mais novo, atualize o `guilda` antes (`guilda self-update`).

Cada caminho gerenciado é classificado comparando o arquivo no disco com a impressão digital do manifesto e com o template novo. Conversão de fim de linha (CRLF/LF) não conta como edição.

| Situação | Plano |
| --- | --- |
| Intacto e o template não mudou | nada |
| Intacto e o template mudou | `write` (atualiza) |
| Editado por você e o template não mudou | `keep` (fica o seu) |
| Editado por você e já igual ao template novo | nada |
| Editado por você e o template também mudou | `conflicts` |
| Apagado por você e ainda no template | `write` (volta) |
| Novo no template, sem arquivo no caminho | `write` |
| Novo no template, com arquivo seu diferente no mesmo caminho | `conflicts` |
| Aposentado pelo template, intacto | `remove` |
| Aposentado pelo template, editado | `conflicts` (aprovado, é removido) |
| Arquivo seu fora do manifesto | nunca tocado |

`--dry-run` só imprime o plano, sem gravar:

```text
write (1):
  .engineering/roles/scribe.md
remove (0):
keep (0):
conflicts (0):
migrate_name: false
```

**Conflitos.** Num terminal interativo, o `upgrade` lista os arquivos, avisa que continuar **sobrescreve sem backup** as alterações locais, sugere `guilda promote` e pergunta `Continuar e sobrescrever? [s/N]` (aceita `s`, `sim`, `y`, `yes`). Sem terminal interativo (script, CI), a lista vai para o stderr e o comando sai com código 1 sem alterar nada. `--yes` aprova sem perguntar. Sem conflitos, não há pergunta.

**Aplicação.** Tudo ou nada: os originais ficam só em memória, o manifesto é gravado por último e, se algo falhar no meio, o projeto é restaurado. Se a própria restauração falhar, o erro lista os arquivos não restaurados. Se o projeto mudar entre o plano e a aplicação, o comando recusa (`stale upgrade plan`). Pastas que ficaram vazias depois de remoções são apagadas.

**Recusas.** Sem manifesto (`no manifest: run guilda init`), manifesto de `package`, instalação mais nova que o template (não faz downgrade) e destino dentro do próprio template.

**Verificação final.** Depois de gravar, o `upgrade` confere que não sobrou nada a gravar, remover ou aprovar. A mensagem `verificação (check): ok` se refere a essa conferência, que aceita os arquivos mantidos; não é o `guilda check` (veja a próxima seção).

```text
atualização concluída em /caminho/meu-projeto
  1 arquivos gravados, 0 removidos, 0 mantidos
  verificação (check): ok
```

Quando o manifesto tinha o nome antigo, aparece também a linha `manifesto migrado para o nome guilda`.

**Migração de projetos antigos.** O manifesto de antes da 2.0.0 se chama `engineering-template`; só o `upgrade` o aceita, e ele o reescreve como `guilda` na mesma operação. A pasta `.engineering/` não muda. Instalações 1.3.0 feitas de um checkout que tinha `core/graphify-out/` registraram `.engineering/graphify-out/` no manifesto: o `upgrade` remove as cópias intactas e deixa as alteradas no disco, fora do manifesto. Mods já instalados não são tocados; mods novos usam o marketplace `guilda-mods`.

```sh
guilda upgrade <projeto> --dry-run   # 1. veja o plano
guilda upgrade <projeto>             # 2. aplique
```

<a id="arquivo-mantido"></a>

## Limitação conhecida: arquivo mantido e o `check`

O `upgrade` mantém um arquivo que você editou quando o template não o mudou, e guarda no manifesto a impressão digital da versão original. O `check --target` e o `install` (numa atualização) continuam estritos: comparam o disco com o manifesto e acusam esse arquivo:

```text
$ guilda check --target meu-projeto
error: installed drift: .engineering/roles/scribe.md
```

Nada está quebrado: o `upgrade` seguinte continua funcionando e mantendo o arquivo. Para o `check` voltar a passar:

1. Guarde a sua alteração (proponha com `guilda promote`, ou copie o arquivo para fora das pastas gerenciadas).
2. Apague ou mova o arquivo.
3. Rode `guilda upgrade <projeto>`: ele regrava a versão do template (`write`) e o `check` passa.

<a id="promote"></a>

## `guilda promote <projeto> --title "..." --description "..." [--yes]`

Propõe suas alterações locais como feature: os arquivos vão para um **gist secreto** e uma **issue** é aberta no repositório do template (fixo no código). Contribuições de terceiros entram só por issue.

**Pré-requisito.** O GitHub CLI (`gh`) instalado e autenticado: o comando começa por `gh auth status` e para se falhar.

**O que entra.** Arquivos em `.engineering/`, `.claude/`, `.codex/` e `.agents/` que você **alterou** (conteúdo diferente do registrado no manifesto, tolerando CRLF/LF) ou **adicionou** (fora do manifesto e que o template não gera).

**O que nunca entra.** O próprio `manifest.json`; qualquer caminho com um segmento `*.local.*` (por exemplo `settings.local.json`); `.claude/worktrees/` e `.claude/projects/`; links simbólicos. A comparação é por segmento de caminho, não por trecho de texto.

**Varredura obrigatória.** Antes de qualquer envio, procura em cada arquivo, no título, na descrição e nos caminhos: tokens conhecidos (GitHub, AWS, Slack, Stripe, Google, JWT, chave privada, `Authorization: Bearer`), atribuições como `password=`/`token:`/`api_key=` com valor que não seja marcador (`<...>`, `${...}`, `changeme`, `xxx`...), credencial em URL, caminhos pessoais (`C:\Users\...`, `/home/...`, `/Users/...`), arquivos binários e arquivos acima de 1 MiB. Qualquer achado bloqueia o envio, mesmo com `--yes`; o relatório mostra só arquivo, linha e tipo, nunca o valor.

**Confirmação.** Mostra os arquivos e tamanhos, e o título e o corpo **exatos** da issue pública (o título ganha o prefixo `[proposta] `). Pergunta `Enviar e abrir a issue? [s/N]`. Sem terminal interativo e sem `--yes`, nada é publicado. `--yes` dispensa só a pergunta, não a varredura.

**O que é publicado.** O gist leva o conteúdo dos arquivos, com `/` trocado por `__` no nome (`.engineering/roles/a.md` vira `.engineering__roles__a.md`). A issue leva a descrição, a lista de caminhos, o link do gist, uma lista de tarefas para o mantenedor e a frase de aceite já marcada: *"Concedo ao mantenedor uma licença ampla para usar, modificar e relicenciar esta contribuição."* Rodar o `promote` e confirmar é concordar com ela.

**Falhas.** Se o gist falhar, nada foi publicado. Se o gist foi criado e a issue falhou, o erro mostra a URL do gist e o comando para apagá-lo (`gh gist delete <id>`); nada é repetido.

**Limitações.**

- `CLAUDE.md` e `AGENTS.md` da raiz não são considerados: só as quatro pastas acima.
- Arquivos que não vieram do template mas estão nessas pastas também entram como "adicionados", por exemplo um mod instalado (`.claude/mods/`, `.claude/scripts/`) ou `.claude/settings.json`. Revise a lista antes de confirmar.
- A issue não recebe label; o prefixo `[proposta]` no título é o que a identifica.
- A varredura é por padrões: reduz o risco, não prova que não há segredo.

<a id="self-update"></a>

## `guilda self-update` e `guilda config`

### `guilda self-update [--dry-run] [--yes]`

Atualiza o próprio `guilda` (o `upgrade` é que atualiza o projeto).

- Se o Python em uso fica no diretório de ferramentas do `uv` (`$UV_TOOL_DIR`, ou um caminho com `uv/tools` ou `uv/data/tools`), roda `uv tool upgrade guilda`; senão, `<python> -m pip install --upgrade guilda`. Sem shell.
- `--dry-run` só imprime `executaria: <comando>`.
- Sem `--yes`, avisa que vai instalar software e pergunta `Continuar? [s/N]`; sem terminal interativo, cancela com código 1 sem executar nada.
- Código de saída do `pip`/`uv` diferente de zero vira `erro: a atualização do guilda falhou (código N)`.

### `guilda config get` e `guilda config set update-check off|notify|auto`

`get` mostra a configuração efetiva em JSON; `set` valida o valor e grava o arquivo de forma atômica.

```json
{
  "update_check": "off",
  "last_check": null
}
```

**Onde fica o arquivo** (`config.json`):

| Situação | Caminho |
| --- | --- |
| Variável `GUILDA_CONFIG` definida | O caminho completo indicado nela |
| Windows | `%APPDATA%\guilda\config.json` |
| Linux, macOS e outros | `$XDG_CONFIG_HOME/guilda/config.json` ou `~/.config/guilda/config.json` |

`GUILDA_CONFIG` aponta o `guilda` para outro arquivo de configuração. A suíte de testes a usa para nunca ler nem gravar o config real do usuário; serve também para isolar o `guilda` num script ou na CI. Arquivo ausente ou inválido equivale aos padrões, sem erro.

**Verificação automática de versão (`update_check`).** Vem desligada (`off`): sem ela, o `guilda` não acessa a rede por conta própria.

- `notify` ou `auto`: no início de `init`, `sync`, `check`, `doctor`, `package`, `install`, `upgrade`, `promote` e `mod`, no máximo uma vez a cada 24 horas, consulta o PyPI (`https://pypi.org/pypi/guilda/json`, 5 s de limite) pela maior versão estável `X.Y.Z` não retirada. `last_check` é gravado antes da consulta, então uma rede fora do ar não gera nova tentativa no mesmo dia. `config`, `self-update` e `--help` nunca fazem a verificação.
- `notify`: se houver versão mais nova, imprime no stderr `guilda X.Y.Z disponível (instalada: ...). Rode: guilda self-update`.
- `auto`: atualiza **na hora, sem perguntar**, com a saída do `pip`/`uv` escondida, e imprime uma linha no stderr (`guilda atualizado para X.Y.Z` ou a falha).
- Qualquer erro da verificação é ignorado: ela nunca derruba o comando.

> [!WARNING]
> **Limitação do `auto`:** a atualização acontece dentro do mesmo processo, logo antes do comando que você pediu, e esse comando continua. Ele roda com o código antigo, já carregado na memória, mas pode ler os arquivos do template que o `pip`/`uv` acabou de trocar no disco. Isso vale até para o `doctor`. Rode o comando de novo depois da atualização, ou prefira `notify` e `guilda self-update` quando quiser. A substituição do executável `guilda` em uso no Windows durante esse fluxo não foi verificada.

<a id="mod"></a>

## `guilda mod <nome> [--scope project|global] [--target <pasta>] [--dry-run]`

Instala um mod do Claude Code de `integrations/mod/` (o mesmo que `guilda install --mod <nome> --mod-scope ...`). O único mod disponível é o [`token-handoff`](../integrations/mod/token-handoff/README.md), e ele só instala no **Windows**; em outro sistema o comando recusa com código 1.

- **Escopo `project`** (padrão): grava em `<target>/.claude/` (`--target` padrão: pasta atual). **Escopo `global`**: grava em `~/.claude/`, para todos os projetos do usuário.
- **O que faz:** copia o mod para `.claude/mods/<nome>/` (sem os arquivos de teste), copia os scripts para `.claude/scripts/`, grava o marketplace local `guilda-mods` em `.claude/mods/.claude-plugin/marketplace.json` e roda `claude plugin marketplace add <pasta> --scope project|user` e `claude plugin install <nome>@guilda-mods --scope project|user`. Reinstalar substitui a pasta do mod.
- **Registro:** acrescenta uma linha em `<target>/docs/operations/registro-instalacoes.md` (criado a partir do modelo, se faltar), também no escopo `global`.
- **Sem o `claude` no PATH, ou se um comando dele falhar:** os arquivos ficam copiados, a linha do registro diz `not verified` e o `guilda` imprime os comandos para rodar à mão. O código de saída continua 0.
- `--dry-run` imprime o aviso do mod, os caminhos e os comandos, sem gravar nada.

Detalhes, remoção e limites em [integrations/mod](../integrations/mod/README.md).

<a id="saida"></a>

## Códigos de saída

| Código | Quando |
| --- | --- |
| 0 | Sucesso, inclusive `--dry-run` e `mod` com o plugin não instalado |
| 1 | Erro de validação ou de execução, conflito não aprovado, confirmação recusada ou sem terminal interativo |
| 2 | Uso inválido (opção obrigatória ausente, valor fora da lista); mensagem do `argparse` |
