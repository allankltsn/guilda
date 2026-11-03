"""Testes da pipeline de release: conferência de versão, de dist/ e portões do workflow."""
import importlib.util
import json
import re
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def _carrega(nome):
    spec = importlib.util.spec_from_file_location(nome, ROOT / "scripts" / f"{nome}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _monta_raiz(tmp: str, template: str, pacote: str) -> Path:
    raiz = Path(tmp)
    (raiz / "guilda").mkdir(exist_ok=True)
    (raiz / "template.json").write_text(json.dumps({"version": template}), encoding="utf-8")
    (raiz / "guilda" / "__version__.py").write_text(f'__version__ = "{pacote}"\n', encoding="utf-8")
    return raiz


def _jobs(texto: str) -> dict[str, str]:
    """Divide o bloco `jobs:` em {nome: texto do job} (jobs com 2 espaços de recuo)."""
    bloco = texto.split("\njobs:\n", 1)[1]
    partes = re.split(r"(?m)^  ([A-Za-z0-9_-]+):\s*$", bloco)
    return {partes[i]: partes[i + 1] for i in range(1, len(partes), 2)}


class CheckReleaseTest(unittest.TestCase):
    def setUp(self):
        self.cr = _carrega("check_release")

    def test_check_release_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _monta_raiz(tmp, "2.0.0", "2.0.0")
            self.assertEqual(self.cr.check("v2.0.0", raiz), [])

    def test_check_release_reports_each_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _monta_raiz(tmp, "2.0.1", "2.0.2")
            problemas = self.cr.check("v2.0.0", raiz)
            self.assertEqual(len(problemas), 2)
            self.assertTrue(any("template.json" in p for p in problemas))
            self.assertTrue(any("__version__" in p for p in problemas))

    def test_tag_malformada(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _monta_raiz(tmp, "2.0.0", "2.0.0")
            for tag in ("2.0", "v2.0.0-rc.1", "v2.0", "", "v01.0.0", "v2.0.0\n", "v1.2.03"):
                with self.subTest(tag=tag):
                    problemas = self.cr.check(tag, raiz)
                    self.assertTrue(any("formato" in p for p in problemas), problemas)

    def test_template_e_pacote_divergentes_com_tag_correta(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _monta_raiz(tmp, "2.0.0", "1.9.0")
            problemas = self.cr.check("v2.0.0", raiz)
            self.assertEqual(len(problemas), 1)
            self.assertIn("__version__", problemas[0])


class CheckDistTest(unittest.TestCase):
    BOM_WHEEL = ["guilda/_data/template.json", "guilda/_data/core/a.md", "guilda-1.0.0.dist-info/LICENSE"]

    def _dist(self, tmp, wheel, sdist):
        d = Path(tmp)
        with zipfile.ZipFile(d / "guilda-1.0.0-py3-none-any.whl", "w") as z:
            for n in wheel:
                z.writestr(n, "x")
        arq = d / "arquivo.txt"
        arq.write_text("x")
        with tarfile.open(d / "guilda-1.0.0.tar.gz", "w:gz") as t:
            for n in sdist:
                t.add(arq, arcname=n)
        return d

    def test_dist_ok(self):
        cd = _carrega("check_dist")
        with tempfile.TemporaryDirectory() as tmp:
            d = self._dist(tmp, self.BOM_WHEEL, ["guilda-1.0.0/PKG-INFO", "guilda-1.0.0/tests/t.py"])
            self.assertEqual(cd.check(d), [])

    def test_dist_rejeita_proibidos_e_faltantes(self):
        cd = _carrega("check_dist")
        with tempfile.TemporaryDirectory() as tmp:
            d = self._dist(
                tmp,
                ["guilda/_data/template.json", "docs/x.md"],
                ["guilda-1.0.0/docs/superpowers/a.md", "guilda-1.0.0/.dev/b"],
            )
            problemas = cd.check(d)
            self.assertTrue(any("wheel" in p and "docs/x.md" in p for p in problemas))
            self.assertTrue(any("sdist" in p and "superpowers" in p for p in problemas))
            self.assertTrue(any("sdist" in p and ".dev" in p for p in problemas))
            self.assertTrue(any("core" in p for p in problemas))
            self.assertTrue(any("LICENSE" in p for p in problemas))

    def test_dist_vazio(self):
        cd = _carrega("check_dist")
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(len(cd.check(Path(tmp))), 2)


class ReleaseWorkflowTest(unittest.TestCase):
    def test_release_workflow_is_gated(self):
        texto = WORKFLOW.read_text(encoding="utf-8")

        # Gatilho: somente push de tags v*.
        on = re.search(r"(?ms)^on:\n(.*?)(?=^\S)", texto).group(1)
        self.assertEqual(
            [l.strip() for l in on.splitlines() if l.strip()],
            ["push:", 'tags: ["v*"]'],
        )

        # Permissões padrão: bloco global inteiro, sem id-token.
        glob = re.search(r"(?ms)^permissions:\n(.*?)(?=^\S)", texto).group(1)
        self.assertEqual(glob, "  contents: read\n\n")

        # Nenhum desvio do portão: sem `if:` nem `continue-on-error`.
        self.assertNotRegex(texto, r"(?m)^\s+(- )?(if|continue-on-error):")

        jobs = _jobs(texto)
        self.assertEqual(set(jobs), {"verify", "build", "publish"})
        publish = jobs["publish"]
        self.assertRegex(publish, r"(?m)^    environment: pypi\s*$")
        self.assertRegex(publish, r"(?m)^    needs: build\s*$")
        self.assertRegex(publish, r"(?m)^      id-token: write\s*$")
        self.assertIn("pypa/gh-action-pypi-publish@", publish)
        self.assertRegex(jobs["build"], r"(?m)^    needs: verify\s*$")

        # id-token aparece uma única vez no arquivo, no job que publica.
        self.assertEqual(texto.count("id-token"), 1)
        com_publicacao = [n for n, t in jobs.items() if "gh-action-pypi-publish" in t]
        self.assertEqual(com_publicacao, ["publish"])
        self.assertNotIn("secrets.", texto)
        self.assertNotIn("password:", texto)
        self.assertNotIn("gh api", texto)
        self.assertNotIn("pending_deployments", texto)

    def test_verify_cobre_matriz_e_confere_distribuicao(self):
        texto = WORKFLOW.read_text(encoding="utf-8")
        jobs = _jobs(texto)
        verify, build = jobs["verify"], jobs["build"]
        self.assertIn("os: [ubuntu-latest, windows-latest]", verify)
        self.assertIn('python-version: ["3.11", "3.12", "3.13"]', verify)
        self.assertIn("fail-fast: false", verify)
        self.assertIn("fetch-depth: 0", verify)
        self.assertIn("scripts/check_release.py", verify)
        self.assertIn("git merge-base --is-ancestor", verify)
        self.assertIn("python -m guilda.payload --check", verify)
        self.assertIn("python -m unittest discover -s tests", verify)
        self.assertIn("python -m unittest tests.test_guilda_wheel", build)
        self.assertIn('python -c "import build"', build)
        self.assertIn("scripts/check_dist.py dist", build)
        self.assertEqual(texto.count("actions/checkout@v4"), texto.count("persist-credentials: false"))


if __name__ == "__main__":
    unittest.main()
