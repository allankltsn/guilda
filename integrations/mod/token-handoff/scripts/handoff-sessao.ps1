# Handoff automatico: abre uma sessao nova do Claude Code com o prompt de continuacao e encerra a sessao que chamou este script.
# Chamado pelo mod contador-tokens-diario via $.process.run (o processo pai deste script e o host da sessao a encerrar).
param(
  [Parameter(Mandatory)] [string] $PromptFile,
  [Parameter(Mandatory)] [string] $Cwd,
  [int] $EsperaSegundos = 3
)
$ErrorActionPreference = 'Stop'

$cwdFull = (Resolve-Path -LiteralPath $Cwd).Path
$arq = (Resolve-Path -LiteralPath $PromptFile).Path
# so aceita prompt dentro do cwd e no formato esperado (evita injecao via caminho)
if (-not $arq.StartsWith($cwdFull, [StringComparison]::OrdinalIgnoreCase)) { throw "prompt fora do cwd: $arq" }
if ((Split-Path $arq -Leaf) -notmatch '^prompt-continuacao-sessao-[A-Za-z0-9_.-]{1,60}\.md$') { throw "nome de prompt invalido" }
if ((Get-Item -LiteralPath $arq).Length -lt 50) { throw "prompt vazio ou curto demais" }

# host da sessao antiga = processo pai deste script
$alvo = (Get-CimInstance Win32_Process -Filter "ProcessId=$PID").ParentProcessId
if (-not $alvo -or $alvo -le 4) { throw "pid do host nao encontrado" }

# 1) sessao nova primeiro, em janela independente (nao morre com a antiga)
$rel = $arq.Substring($cwdFull.Length).TrimStart('\', '/').Replace('\', '/')
$msg = "Leia $rel e continue a partir dali. Siga o prompt de continuacao a risca."
if (Get-Command wt.exe -ErrorAction SilentlyContinue) {
  Start-Process wt.exe -ArgumentList @('-d', "`"$cwdFull`"", 'claude', "`"$msg`"")
} else {
  Start-Process powershell.exe -WorkingDirectory $cwdFull -ArgumentList @('-NoExit', '-Command', "claude '$msg'")
}

# 2) depois, mata so o host antigo (sem arvore), por um processo separado e oculto, com pequena espera para o disco assentar
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
  '-NoProfile', '-Command', "Start-Sleep -Seconds $EsperaSegundos; Stop-Process -Id $alvo -Force -ErrorAction SilentlyContinue"
)
Write-Output "handoff ok: novo prompt=$rel, encerrando pid=$alvo em ${EsperaSegundos}s"
