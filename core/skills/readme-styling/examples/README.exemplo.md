<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero.svg">
  <img alt="Meu Projeto: API em Python com pipeline de CI e deploy em contêiner" src="assets/hero.svg" width="100%">
</picture>

<p align="center">
  <a href="https://exemplo.dev/docs"><img src="https://img.shields.io/badge/Docs-0ea5a4?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Documentação"></a>&nbsp;
  <a href="https://github.com/org/meu-projeto/issues"><img src="https://img.shields.io/badge/Issues-2dd4bf?style=for-the-badge&logo=github&logoColor=black" alt="Issues"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-0ea5a4?style=flat-square" alt="Versão">
  <img src="https://img.shields.io/badge/license-MIT-16a34a?style=flat-square" alt="Licença">
  <img src="https://img.shields.io/badge/python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
</p>

---

Meu Projeto expõe uma API de pedidos para equipes que hoje controlam tudo em planilhas. Valida o
pedido, grava no PostgreSQL e publica o evento para os demais serviços.

## <img src="assets/icons/teal/rocket.svg" width="22" align="top"> Início rápido

```bash
git clone https://github.com/org/meu-projeto && cd meu-projeto
docker compose up -d        # API + PostgreSQL
curl localhost:8000/health  # {"status":"ok"}
```

## <img src="assets/icons/teal/workflow.svg" width="22" align="top"> Como funciona

<img alt="Fluxo: requisição, validação, gravação, evento publicado" src="assets/fluxo-pedido.svg" width="100%">

- **Valida na borda.** Esquema rejeita pedido inválido antes de tocar o banco.
- **Grava e publica juntos.** Transação com outbox evita evento sem pedido.
- **Observável.** Logs JSON com id de requisição e endpoint de saúde com versão.

## <img src="assets/icons/teal/layers.svg" width="22" align="top"> Recursos

<table>
  <tr>
    <td width="50%" valign="top">
      <h3><img src="assets/icons/teal/shield-check.svg" width="20" align="top"> Segurança</h3>
      <p>JWT com revogação e limite de taxa por cliente. <code>FastAPI</code> <code>Redis</code></p>
    </td>
    <td width="50%" valign="top">
      <h3><img src="assets/icons/teal/database.svg" width="20" align="top"> Persistência</h3>
      <p>Migrações versionadas e índices pelos filtros reais. <code>PostgreSQL</code></p>
    </td>
  </tr>
</table>

## <img src="assets/icons/teal/terminal.svg" width="22" align="top"> Uso

```python
from meu_projeto import Cliente

pedido = Cliente("http://localhost:8000").criar_pedido(item="X-1", quantidade=2)
print(pedido.id)
```

---

<sub>MIT · feito com a skill readme-styling</sub>
