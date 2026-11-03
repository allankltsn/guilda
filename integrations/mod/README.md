# Mods do Claude Code

Mods são plugins locais (hooks que mudam o comportamento da sessão). Cada pasta de `integrations/mod/<nome>/`
é um mod completo: `.claude-plugin/plugin.json`, `hooks/` e, quando precisa, `types/` e `scripts/`.
Eles **não** são copiados para `.engineering/` pela instalação normal do template; só entram pela flag `--mod`.

## Instalar

```bash
guilda mod token-handoff --target <projeto>                   # só neste projeto (padrão: --scope project)
guilda mod token-handoff --target <projeto> --scope global    # todos os projetos do usuário (~/.claude)
guilda mod token-handoff --target <projeto> --dry-run         # mostra o que faria, sem gravar
guilda install <projeto> --mod token-handoff [--mod-scope global]   # junto com a instalação do template
```

Sem `--target`, `guilda mod` usa a pasta atual. No checkout, `python install.py <projeto> --mod <nome>` equivale a
`guilda install <projeto> --mod <nome>`. `--mod` é repetível e vem depois da instalação (ou atualização) do template
no mesmo comando; se o mod falhar, o template já foi gravado. O comando é a
aprovação explícita exigida por `policies/installations.md`: o instalador imprime o aviso do mod, grava os
arquivos, instala o plugin pelo próprio Claude Code e acrescenta uma linha a
`docs/operations/registro-instalacoes.md` do projeto (criando o arquivo, se faltar).

Passo a passo interno, por mod:
1. copia o mod para `<escopo>/.claude/mods/<nome>` (sem testes) e seus scripts para `<escopo>/.claude/scripts/`;
2. grava `<escopo>/.claude/mods/.claude-plugin/marketplace.json` (marketplace local `guilda-mods`);
3. roda `claude plugin marketplace add <escopo>/.claude/mods --scope project|user` e
   `claude plugin install <nome>@guilda-mods --scope project|user`.

`<escopo>` é o projeto (`--scope project`/`--mod-scope project`) ou o diretório do usuário (`--scope global`/
`--mod-scope global`, `~/.claude`). O registro de instalações fica sempre no projeto de destino, também no escopo
global. Reinstalar substitui a pasta do mod. Mod marcado como só Windows é recusado nos outros sistemas, sem gravar
nada.
Se o `claude` não estiver no PATH ou o comando falhar, os arquivos ficam copiados, a linha do registro diz
`not verified`, o instalador imprime os comandos para rodar à mão e o código de saída continua 0.

## Remover

```bash
claude plugin uninstall <nome>@guilda-mods --scope project   # ou: --scope user
```

Depois apague `<escopo>/.claude/mods/<nome>` e os scripts listados no registro de instalações.

## Limites conhecidos
- Escopo `project` grava o caminho absoluto da pasta em `.claude/settings.json` (`extraKnownMarketplaces`): ao
  versionar esse arquivo, outra máquina precisa rodar o instalador de novo.
- Os mods são testados por unidade (`claude plugin test`), não por sessão real de ponta a ponta.
- A linha do registro de instalações sempre diz `via install.py --mod <nome>`, mesmo quando o mod foi instalado por
  `guilda mod` ou `guilda install --mod`.

## Mods disponíveis

| Mod | O que faz | Plataforma |
|---|---|---|
| [token-handoff](token-handoff/README.md) | Aos 400k tokens grava o prompt de continuação, abre a sessão nova com ele e encerra a atual, sem perguntar ao humano. | Windows (PowerShell e Windows Terminal) |

## Criar outro mod
1. Crie `integrations/mod/<nome>/` com `.claude-plugin/plugin.json` e `hooks/` (use `claude plugin validate` e
   `claude plugin test`).
2. Registre o mod em `MODS` em `guilda/mods.py` (resumo, aviso, plataforma e scripts a copiar).
3. Rode `python -m guilda.payload --write` para o mod entrar na allowlist do pacote (sem isso ele não vai no wheel).
4. Acrescente um teste em `tests/test_template.py` e a linha da tabela acima.
