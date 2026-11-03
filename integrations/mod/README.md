# Mods do Claude Code

Mods são plugins locais (hooks que mudam o comportamento da sessão). Cada pasta de `integrations/mod/<nome>/`
é um mod completo: `.claude-plugin/plugin.json`, `hooks/` e, quando precisa, `types/` e `scripts/`.
Eles **não** são copiados para `.engineering/` pela instalação normal do template; só entram pela flag `--mod`.

## Instalar

```bash
python install.py <projeto> --mod token-handoff                      # só neste projeto (padrão)
python install.py <projeto> --mod token-handoff --mod-scope global   # todos os projetos do usuário
python install.py <projeto> --mod token-handoff --dry-run            # mostra o que faria, sem gravar
```

`--mod` é repetível e vem depois da instalação (ou atualização) do template no mesmo comando. O comando é a
aprovação explícita exigida por `policies/installations.md`: o instalador imprime o aviso do mod, grava os
arquivos, instala o plugin pelo próprio Claude Code e acrescenta uma linha a
`docs/operations/registro-instalacoes.md` do projeto (criando o arquivo, se faltar).

Passo a passo interno, por mod:
1. copia o mod para `<escopo>/.claude/mods/<nome>` (sem testes) e seus scripts para `<escopo>/.claude/scripts/`;
2. grava `<escopo>/.claude/mods/.claude-plugin/marketplace.json` (marketplace local `engineering-template-mods`);
3. roda `claude plugin marketplace add <escopo>/.claude/mods --scope project|user` e
   `claude plugin install <nome>@engineering-template-mods --scope project|user`.

`<escopo>` é o projeto (`--mod-scope project`) ou o diretório do usuário (`--mod-scope global`, `~/.claude`).
Se o `claude` não estiver no PATH ou o comando falhar, os arquivos ficam copiados, a linha do registro diz
`not verified` e o instalador imprime os comandos para rodar à mão.

## Remover

```bash
claude plugin uninstall <nome>@engineering-template-mods --scope project   # ou: --scope user
```

Depois apague `<escopo>/.claude/mods/<nome>` e os scripts listados no registro de instalações.

## Limites conhecidos
- Escopo `project` grava o caminho absoluto da pasta em `.claude/settings.json` (`extraKnownMarketplaces`): ao
  versionar esse arquivo, outra máquina precisa rodar o instalador de novo.
- Os mods são testados por unidade (`claude plugin test`), não por sessão real de ponta a ponta.

## Mods disponíveis

| Mod | O que faz | Plataforma |
|---|---|---|
| [token-handoff](token-handoff/README.md) | Aos 400k tokens grava o prompt de continuação, abre a sessão nova com ele e encerra a atual, sem perguntar ao humano. | Windows (PowerShell e Windows Terminal) |

## Criar outro mod
1. Crie `integrations/mod/<nome>/` com `.claude-plugin/plugin.json` e `hooks/` (use `claude plugin validate` e
   `claude plugin test`).
2. Registre o mod em `MODS` em `scripts/mods.py` (resumo, aviso, plataforma e scripts a copiar).
3. Acrescente um teste em `tests/test_template.py` e a linha da tabela acima.
