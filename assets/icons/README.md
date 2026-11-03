# Ícones (Lucide)

Biblioteca completa do [Lucide](https://lucide.dev/) (v1.65.0, licença ISC, ver [LICENSE](LICENSE)) em
[`lucide/`](lucide/): 2275 SVGs 24×24, traço `currentColor`, `stroke-width` 2, pontas arredondadas.
É o único conjunto de ícones do projeto; não misturar com emoji nem outras famílias.

## Uso padronizado

O GitHub não aplica CSS em `<img src="x.svg">`, então `currentColor` fica preto. Gere uma cópia
colorida com o script da skill `readme-styling` e referencie a cópia:

```bash
python core/skills/readme-styling/scripts/lucide_icon.py rocket shield-check --color "#2dd4bf" --out-dir assets/icons/teal
```

```html
<img src="assets/icons/teal/rocket.svg" width="20" align="top"> Início rápido
```

Procurar um ícone: `python core/skills/readme-styling/scripts/lucide_icon.py --list git`.

## Conjunto padrão por assunto

Use estes nomes antes de procurar outros. Mesmo assunto, mesmo ícone em todos os documentos.

| Assunto | Ícones |
|---|---|
| Início, entrega | `rocket` `package` `package-open` `download` `upload` `play` `flag` |
| Fluxo, processo | `workflow` `git-branch` `git-merge` `git-pull-request` `git-commit-horizontal` `refresh-cw` `arrow-right` `list-checks` |
| Código | `terminal` `code-xml` `file-code` `file-text` `blocks` `puzzle` `plug` `bug` |
| Arquitetura, infra | `layers` `network` `server` `database` `cloud` `container` `cpu` `globe` `settings` `wrench` `hammer` |
| Segurança, conformidade | `shield-check` `shield-alert` `lock` `key-round` `scale` `gavel` `eye` |
| Qualidade, métricas | `circle-check` `circle-x` `triangle-alert` `info` `gauge` `activity` `chart-column` `chart-pie` `chart-line` `flask-conical` `test-tube` `clipboard-check` `target` |
| Pessoas, agentes | `users` `user` `bot` `brain` `sparkles` `lightbulb` |
| Documentação, navegação | `book-open` `folder-tree` `search` `map` `compass` `link` `bookmark` `tag` `star` `heart` `calendar` `clock` `mail` |
| Interface | `monitor` `smartphone` `palette` `image` |

## Cores

Mesma paleta da skill `dark-pipeline-svg`, para que ícones, diagramas e banners pareçam um só sistema:

| Uso | Cor |
|---|---|
| Destaque (padrão) | `#2dd4bf` |
| Secundário | `#60a5fa` |
| Sucesso | `#4ade80` |
| Atenção | `#f59e0b` |
| Erro, risco | `#ef4444` |
| Neutro | `#8b96a8` |
