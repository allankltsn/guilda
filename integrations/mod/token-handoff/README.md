# token-handoff

Mod do Claude Code. Conta os tokens da sessão (contexto principal mais subagentes) e age **só aos 400k**. Não
existem marcos de 100k, 200k ou 300k e o mod nunca pergunta nada ao humano.

## O que acontece aos 400k
1. Novos despachos de agente são negados; os agentes em andamento terminam.
2. O mod injeta no modelo o protocolo: registrar a memória do projeto e gravar
   `docs/operations/prompt-continuacao-sessao-<AAAA-MM-DD>.md`.
3. No fim do turno, com o arquivo gravado e nenhum agente ativo, o mod roda `handoff-sessao.ps1`, que abre uma
   sessão nova do Claude Code (Windows Terminal) com `Leia <prompt> e continue` e, depois, encerra o processo
   da sessão antiga (só ele, sem a árvore). A tentativa acontece uma vez por sessão.

Também grava linhas em `docs/operations/diario-sessao-AAAA-MM-DD.mod.md` (arquivo próprio do mod, só se existir
`.engineering/project.json`), no despacho e no fim de agentes e no marco.

## Instalar
`python install.py <projeto> --mod token-handoff [--mod-scope global]`; veja [integrations/mod](../README.md).
Desligar: `claude plugin disable token-handoff@engineering-template-mods`.

## Requisitos e permissões
- Windows com PowerShell e `wt.exe` (sem `wt`, abre uma janela do PowerShell).
- Executa `powershell.exe` com o script de `<projeto>/.claude/scripts/` ou, na falta dele, `~/.claude/scripts/`.
- Sem rede. Grava só o diário do mod e o prompt de continuação que o próprio modelo escreve.

## Limitações conhecidas
- O PID da sessão antiga é o do processo pai do script. Isso decorre da API do mod e **não foi verificado em
  sessão real**; teste com um limite baixo antes de confiar.
- Na extensão do VSCode, encerrar o processo deixa a aba antiga com erro; a sessão nova abre no terminal.
- O total de tokens é uma estimativa: soma dos incrementos positivos de `context.tokens` mais os tokens de subagentes.
  A compactação não subtrai nem redispara o marco.
- Duas sessões simultâneas no mesmo cwd e dia podem perder linhas do diário (sem trava entre escritores).
- Se o modelo não gravar o prompt com o nome esperado, nada é aberto nem encerrado.
