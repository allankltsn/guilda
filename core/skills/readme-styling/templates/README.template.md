<!--
Modelo de README da skill readme-styling. Troque cada {{PLACEHOLDER}}, apague as seções que não se
aplicam e remova este comentário. Gere os SVGs com a dark-pipeline-svg (hero.py, chart.py) e os
ícones com scripts/lucide_icon.py. Cartões de código: scripts/code_card.py.
-->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero.svg">
  <img alt="{{NOME}}: {{DESCRIÇÃO CURTA DO QUE O BANNER MOSTRA}}" src="assets/hero.svg" width="100%">
</picture>

<p align="center">
  <a href="{{URL_DOCS}}"><img src="https://img.shields.io/badge/Docs-0ea5a4?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Documentação"></a>&nbsp;
  <a href="{{URL_REPO}}/issues"><img src="https://img.shields.io/badge/Issues-2dd4bf?style=for-the-badge&logo=github&logoColor=black" alt="Issues"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/versão-{{VERSÃO}}-0ea5a4?style=flat-square" alt="Versão">
  <img src="https://img.shields.io/badge/licença-{{LICENÇA}}-16a34a?style=flat-square" alt="Licença">
  <img src="https://img.shields.io/badge/{{STACK}}-{{VERSÃO_STACK}}-3776AB?style=flat-square&logo={{LOGO_SIMPLE_ICONS}}&logoColor=white" alt="{{STACK}}">
</p>

---

{{RESUMO: o que é, para quem, qual problema resolve, em 2 a 4 linhas.}}

## <img src="assets/icons/teal/sparkles.svg" width="22" align="top"> Recursos

<table>
  <tr>
    <td width="50%" valign="top">
      <h3><img src="assets/icons/teal/{{ICONE_1}}.svg" width="20" align="top"> {{RECURSO 1}}</h3>
      <p>{{Uma frase sobre o que entrega.}} <code>{{chave}}</code> <code>{{chave}}</code></p>
    </td>
    <td width="50%" valign="top">
      <h3><img src="assets/icons/teal/{{ICONE_2}}.svg" width="20" align="top"> {{RECURSO 2}}</h3>
      <p>{{Uma frase sobre o que entrega.}} <code>{{chave}}</code> <code>{{chave}}</code></p>
    </td>
  </tr>
</table>

## <img src="assets/icons/teal/rocket.svg" width="22" align="top"> Início rápido

<img alt="Comandos de instalação e verificação" src="assets/codigo/inicio-rapido.svg">

<details>
<summary>Copiar comandos</summary>

```bash
{{COMANDO 1}}
{{COMANDO 2}}
```

</details>

## <img src="assets/icons/teal/workflow.svg" width="22" align="top"> Como funciona

<img alt="{{O QUE O DIAGRAMA MOSTRA}}" src="assets/fluxo-{{ASSUNTO}}.svg" width="100%">

- **{{Ponto 1}}.** {{Explicação em uma frase.}}
- **{{Ponto 2}}.** {{Explicação em uma frase.}}
- **{{Ponto 3}}.** {{Explicação em uma frase.}}

> [!NOTE]
> {{Informação útil que o leitor não pode perder.}}

## <img src="assets/icons/teal/gauge.svg" width="22" align="top"> Números

<img alt="{{O QUE O GRÁFICO MOSTRA, COM OS VALORES}}" src="assets/graficos/{{ASSUNTO}}.svg" width="60%">

## <img src="assets/icons/teal/terminal.svg" width="22" align="top"> Uso

```{{LINGUAGEM}}
{{EXEMPLO CURTO E EXECUTÁVEL}}
```

## <img src="assets/icons/teal/folder-tree.svg" width="22" align="top"> Estrutura

<details>
<summary><b>Árvore do repositório</b></summary>

```
{{RAIZ}}/
├── {{PASTA}}/     {{PARA QUE SERVE}}
└── {{ARQUIVO}}    {{PARA QUE SERVE}}
```

</details>

## <img src="assets/icons/teal/git-branch.svg" width="22" align="top"> Contribuir e licença

{{Como contribuir em 1 ou 2 linhas.}} Licença {{LICENÇA}}.
