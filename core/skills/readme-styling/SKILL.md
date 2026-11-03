---
name: readme-styling
description: Escreve ou reestiliza README.md e outros markdowns de projeto com visual de portfólio profissional, sem perder clareza: banner SVG animado no topo, badges, tópicos bem separados, grids em tabela HTML, diagramas e gráficos em SVG animado, blocos de código com coloração e ícones Lucide padronizados. Use sempre que o usuário pedir para criar, melhorar, embelezar, estilizar ou "deixar bonito" um README, página de perfil do GitHub, documentação de projeto ou changelog visual, mesmo que ele não diga "skill" nem cite SVG.
---

# README estilizado

Um README bem estilizado é uma página de apresentação: quem chega entende em 10 segundos o que o projeto é, em 1 minuto como ele funciona e em 5 como rodá-lo. O estilo existe para servir essa leitura (separar assuntos, mostrar em imagem o que seria um parágrafo confuso), nunca para enfeitar. Cada elemento abaixo tem um trabalho; se não tiver, não entra.

Esta skill orquestra três coisas que já existem no projeto:

| Peça | De onde vem |
|---|---|
| Banner, diagramas, gráficos animados | skill `dark-pipeline-svg` (`scripts/hero.py`, `scripts/chart.py`, diagramas à mão) |
| Cartões de código, árvore e tabela | `scripts/code_card.py` e `scripts/table_card.py` desta skill |
| Ponto de partida do README | `templates/README.template.md` desta skill |
| Ícones | `assets/icons/lucide/` + `scripts/lucide_icon.py` desta skill; conjunto padrão em `assets/icons/README.md` |
| Badges, grids, código, estrutura | este arquivo |

## Fluxo

1. **Entender o projeto antes de estilizar.** Leia o código, manifestos e o README atual. Todo número, comando e nome de stack no README precisa existir de fato; estilo não autoriza inventar.
2. **Montar o esqueleto** (seção 1; copie `templates/README.template.md` como base) e decidir, por seção, qual recurso visual cabe (seção 2).
3. **Gerar os SVGs** com a skill `dark-pipeline-svg` e salvar em `assets/` do projeto alvo (ver seção 6 para nomes).
4. **Gerar os ícones** coloridos com `lucide_icon.py`.
5. **Escrever o markdown**, seguindo os padrões das seções 3 a 5.
6. **Conferir** com o checklist da seção 7.

## 1. Esqueleto

Ordem que funciona para a maioria dos projetos; omita o que não se aplica.

1. **Banner** (SVG animado, `<picture>` se houver variante clara).
2. **Badges** em duas linhas: links/ações (centralizados) e estado (versão, licença, CI, stack).
3. **Resumo** em 2 a 4 linhas: o que é, para quem, qual problema resolve.
4. **Início rápido**: o menor caminho até ver funcionando (3 a 6 comandos).
5. **Como funciona**: diagrama animado + 3 a 5 bullets em negrito.
6. **Recursos / stack**: grid de cards ou tabela.
7. **Uso e exemplos**: blocos de código com linguagem.
8. **Estrutura do repositório** (árvore curta) e **contribuição/licença**.

Separe os tópicos com `##` e uma régua `---` apenas entre blocos grandes (depois do cabeçalho, antes do rodapé). Régua demais cria ruído.

## 2. Qual recurso para qual conteúdo

| Conteúdo | Recurso | Motivo |
|---|---|---|
| Identidade do projeto | Banner `hero.py` | Primeira impressão, mostra a stack em um olhar |
| Fluxo, pipeline, arquitetura | Diagrama SVG animado | A animação mostra a ordem dos passos, o que o texto faz mal |
| Proporções (linguagens, cobertura, custo) | Gráfico `chart.py` (`stacked`, `bars`, `donut`) | Comparar quantidades é visual |
| 3 a 6 itens paralelos (recursos, projetos) | Grid em `<table>` | Escaneável lado a lado |
| Comparação com várias dimensões | Tabela markdown | Simples e acessível |
| Comandos, config, saída | Bloco de código com linguagem; cartão SVG nos destaques | Botão de copiar; cartão para cor consistente |
| Estado, versão, tecnologia | Badge | Informação curta e atualizada pela origem |
| Cabeçalho de seção, item de card | Ícone Lucide de 20 px | Âncora visual consistente |

Se um parágrafo descreve etapas em sequência ou componentes ligados entre si, é candidato a diagrama. Se descreve 3 ou mais itens com os mesmos atributos, é candidato a grid.

## 3. Banner e imagens SVG

O GitHub exibe SVG em `<img>` e preserva animação SMIL, mas bloqueia script e fonte externa. Por isso os SVGs desta família são autocontidos (sem `<script>`, sem `@import`).

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero.svg">
  <img alt="Nome do projeto: descrição curta do que o banner mostra" src="assets/hero.svg" width="100%">
</picture>
```

- Escreva `alt` descritivo: ele é o que leitores de tela e o README sem imagem mostram.
- Os SVGs são dark. Em tema claro eles seguem legíveis por terem fundo próprio; só crie variante clara se o usuário pedir.
- Use caminho relativo (`assets/...`) para funcionar em clone, fork e no GitHub.
- Gere com `python <skill dark-pipeline-svg>/scripts/hero.py projeto.json assets/hero.svg` (sem `--html`; o `.svg` puro é o que o README embute).

## 4. Ícones Lucide

Use somente `assets/icons/lucide/`. Gere a cópia colorida (o `currentColor` do original fica preto no GitHub dark):

```bash
python <skill readme-styling>/scripts/lucide_icon.py rocket package workflow --color "#2dd4bf" --out-dir assets/icons/teal
```

Em cabeçalhos, o ícone vai inline antes do texto:

```markdown
## <img src="assets/icons/teal/rocket.svg" width="22" align="top"> Início rápido
```

Se o projeto alvo ainda não tem `assets/icons/lucide/`, copie-o do Engineering Template ou extraia de `npm pack lucide-static` (pasta `icons/`, mais o `LICENSE`) antes de gerar os ícones.

Escolha o nome em `assets/icons/README.md` (conjunto padrão por assunto) antes de procurar outro, para que o mesmo assunto tenha o mesmo ícone em todo o projeto. Use no máximo uma cor de destaque por documento, mais verde/âmbar/vermelho só para estado. Nunca misture emoji ou outra família de ícones.

## 5. Padrões de markdown

### Badges (shields.io)

Estilo `for-the-badge` para links de ação no topo, `flat-square` para estado e stack. Mantenha um só estilo por linha.

```html
<p align="center">
  <a href="URL"><img src="https://img.shields.io/badge/Docs-0ea5a4?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Docs"></a>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/version-1.3.0-0ea5a4?style=flat-square" alt="Versão">
  <img src="https://img.shields.io/badge/license-MIT-16a34a?style=flat-square" alt="Licença">
</p>
```

Espaço em texto de badge é `%20`; hífen literal é `--`; underline literal é `__`. Badge de CI ou cobertura só entra se o serviço existe; badge inventado engana o leitor.

### Grid de cards

`<table>` com `valign="top"` é o único grid que o GitHub renderiza de forma confiável. Duas colunas de 50% costumam ser o ideal; três só para cards muito curtos.

```html
<table>
  <tr>
    <td width="50%" valign="top">
      <h3><img src="assets/icons/teal/shield-check.svg" width="20" align="top"> Segurança</h3>
      <p>Uma frase sobre o que entrega. <code>stack</code> <code>chave</code></p>
    </td>
    <td width="50%" valign="top">
      <h3><img src="assets/icons/teal/workflow.svg" width="20" align="top"> Fluxo</h3>
      <p>Uma frase sobre o que entrega. <code>stack</code> <code>chave</code></p>
    </td>
  </tr>
</table>
```

Dentro de `<td>` use tags HTML, não markdown: o GitHub não processa markdown dentro de bloco HTML sem linha em branco, e a linha em branco quebra o layout.

### Código com coloração

O GitHub escolhe o tema dos blocos sozinho e quase não colore comandos de CLI (só palavras-chave da linguagem), e nada no markdown muda isso. Por isso há dois níveis:

1. **Bloco comum** para tudo: sempre informe a linguagem na cerca (`bash`, `python`, `yaml`, `json`, `ts`, `diff`; `console` para sessão com prompt e saída). Um bloco por intenção, com um comentário de uma linha quando o comando não for óbvio. Use `diff` para mostrar mudança e `yaml` para resumir configuração. Blocos com mais de ~25 linhas ficam em `<details>`.
2. **Cartão SVG** só para os blocos de destaque (início rápido, exemplo principal), gerado com `scripts/code_card.py`, que fixa as cores do projeto:

```bash
python <skill readme-styling>/scripts/code_card.py comandos.txt assets/codigo/inicio-rapido.svg --lang bash --title "Instalar"
```

O cartão é imagem, então não dá para copiar nem o leitor de tela lê o código. Compense sempre: `alt` descrevendo o que os comandos fazem e o mesmo texto em bloco comum logo abaixo, dentro de `<details><summary>Copiar comandos</summary>`. Sem o bloco copiável, o cartão atrapalha mais do que ajuda. O cartão é estático por padrão (`--anim` revela linha a linha, mas só use onde o texto copiável abaixo já garante a informação). Linguagens do cartão: `tree` (árvore de diretórios), `bash`, `console`, `python`, `yaml`, `json`, `text`.

### Tabelas e árvores com visual do projeto

Tabela markdown e árvore em bloco de código herdam o tema do GitHub. Para as que são parte central da página (opções de comando, perfis, árvore do repositório), gere cartões com o mesmo critério dos de código: imagem para o visual, texto copiável abaixo em `<details>`.

```bash
python <skill readme-styling>/scripts/table_card.py tabela.md assets/tabelas/opcoes.svg --title "Opções"
python <skill readme-styling>/scripts/code_card.py arvore.txt assets/codigo/arvore.svg --lang tree --title "projeto/"
```

`table_card.py` lê a própria tabela markdown (`` `código` `` vira mono teal, `**negrito**` vira branco) e quebra texto longo em linhas. Use só em tabelas com no máximo ~12 linhas e sem links dentro das células, porque o SVG não leva links. Tabela de referência com links (índice de diagramas, por exemplo) continua em markdown.

### Blocos de destaque

```markdown
> [!NOTE]
> Informação útil.

> [!WARNING]
> Risco real, com a consequência.
```

Use no máximo um ou dois por página; destaque em tudo vira ruído.

### Texto

- Bullets com termo em negrito, ponto, explicação: `- **Verificar toda mudança.** CI roda lint, tipos e testes antes do merge.`
- Frases diretas, voz ativa, sem adjetivos de marketing. Dado concreto vale mais que "poderoso" ou "robusto".
- Escreva no idioma do projeto; não misture PT e EN no mesmo README.
- Evite travessão como pontuação; prefira vírgula, ponto ou dois-pontos.

## 6. Organização de arquivos no projeto alvo

```
README.md
assets/
├── hero.svg                # banner
├── codigo/<assunto>.svg    # cartões de código e de árvore
├── tabelas/<assunto>.svg   # cartões de tabela
├── fluxo-<assunto>.svg     # diagramas
├── grafico-<assunto>.svg   # gráficos
└── icons/
    └── teal/*.svg          # ícones Lucide recoloridos (só os usados)
```

Mantenha em `assets/icons/<cor>/` somente os ícones que o README usa; a biblioteca completa fica em `assets/icons/lucide/`. Um README é o ponto de partida: para outros markdowns (guias, changelog, ADR) use o mesmo vocabulário visual, mas só cabeçalhos com ícone, tabelas, código e callouts. Banner e diagramas ficam para a página inicial e para guias que realmente precisem deles.

## 7. Checklist

- [ ] Primeira tela mostra banner, badges e resumo, e o resumo responde "o que é".
- [ ] Início rápido roda como escrito (comandos conferidos, não presumidos).
- [ ] Cada seção tem um papel claro; nenhum SVG ou ícone decorativo sem função.
- [ ] Todo SVG tem `alt`, caminho relativo e abre sozinho no navegador sem erro.
- [ ] Ícones vêm só de `assets/icons/lucide/`, na cor da paleta, com nome do conjunto padrão.
- [ ] Todo bloco de código tem linguagem na cerca; todo cartão SVG (código, árvore, tabela) tem o texto copiável logo abaixo.
- [ ] Grid renderiza com HTML puro dentro das células.
- [ ] Números, versões e nomes de stack batem com o repositório.
- [ ] Links e imagens relativos funcionam a partir da raiz do repositório.

Modelo em branco: `templates/README.template.md`. Exemplo preenchido e mínimo: `examples/README.exemplo.md`.
