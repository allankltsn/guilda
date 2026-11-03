# Adapter Claude

A instalação de projeto é preferencial: guilda init --providers claude (ou
guilda install) materializa
.claude/agents, comandos, skills, CLAUDE.md e .engineering gerenciada.
Não instala configurações globais nem permissões de bypass. Agentes de revisão
omitem Write/Edit; Bash diagnóstico é contrato de leitura, não sandbox de
comandos. O escopo de escrita de QA também é contrato textual. Ferramentas e
permissões reais dependem do host de destino.

## Consumo do plugin com contratos compartilhados

guilda package --provider claude --target <diretorio-separado> (no checkout:
python scripts/template.py package ...) gera agents/, commands/,
skills/, .claude-plugin/plugin.json, metadados de marketplace, .engineering/ e
BOOTSTRAP.md na raiz do pacote. Gerar ou copiar esses arquivos não instala nem
habilita o plugin. Os agentes nativos continuam no plugin; não são copiados
para .claude/agents do consumidor.

As instruções COMMON acessam .engineering relativamente à raiz do projeto
consumidor. Portanto ler apenas BOOTSTRAP.md não basta. Para usar o plugin:

1. Revise o pacote e escolha o projeto consumidor. Se esse projeto já contém
   .engineering, aborte este fluxo: use a instalação de projeto pela CLI init
   e seu tratamento explícito de conflitos, sem habilitar plugin duplicado.
   Não misture os dois layouts.
2. Copie a árvore .engineering do pacote para a raiz do consumidor, excluindo
   somente seu manifest.json de raiz. O comando abaixo falha se o destino já
   existir; substitua os dois caminhos e revise-os antes de executar.
3. Copie o conteúdo de BOOTSTRAP.md do pacote para CLAUDE.md na raiz do consumidor.
   Se CLAUDE.md já existir, mescle explicitamente as instruções após revisão;
   preserve as instruções do projeto e resolva conflitos. Não suponha
   carregamento automático.
4. Instale e habilite o plugin pelo mecanismo suportado pela sua versão do
   Claude, em ação separada e autorizada. Inicie a sessão na raiz do consumidor
   e confirme a leitura de CLAUDE.md e dos contratos referenciados.

Comando PowerShell com Python 3.11+ e biblioteca padrão:

```powershell
@'
import argparse
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("plugin_root")
parser.add_argument("consumer_root")
args = parser.parse_args()
plugin = Path(args.plugin_root).resolve(strict=True)
consumer = Path(args.consumer_root).resolve(strict=True)
common = plugin / ".engineering"
destination = consumer / ".engineering"
if not common.is_dir() or not (plugin / "BOOTSTRAP.md").is_file():
    parser.error("Pacote incompleto: faltam .engineering ou BOOTSTRAP.md")
if not consumer.is_dir() or destination.exists() or destination.is_symlink():
    parser.error("Destino deve ser um projeto existente sem .engineering")
shutil.copytree(
    common,
    destination,
    ignore=lambda folder, names: {"manifest.json"} if Path(folder) == common else set(),
)
print("Contratos copiados; agora revise e mescle BOOTSTRAP.md em CLAUDE.md.")
'@ | python - 'C:\caminho\plugin-revisado' 'C:\caminho\projeto-consumidor'
```

Essa cópia é uma exportação de contratos para leitura, não uma instalação
gerenciada pela CLI. Não execute check ou sync apontando para o consumidor
desse fluxo: não há manifesto gerenciado nele. Esses comandos continuam
aplicáveis à raiz do pacote plugin, que mantém seu manifesto. Para atualizar
os contratos exportados, revise uma nova versão e faça uma substituição manual
controlada, ou migre explicitamente para instalação de projeto. Não use
copytree com sobrescrita nem misture manifestos.

Não presuma que permissionMode/hooks/mcpServers de agentes de plugin imponham
restrições; este adapter não emite esses campos. A presença dos recursos e sua
leitura podem ser verificadas numa fixture, mas não comprovam descoberta,
invocação ou permissões de agentes nativos no Claude.

Fontes: [referência de plugins](https://code.claude.com/docs/en/plugins-reference)
e [subagentes](https://code.claude.com/docs/en/sub-agents).
