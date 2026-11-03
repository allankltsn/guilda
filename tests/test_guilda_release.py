"""Testes da pipeline de release: conferência de versão e portões do workflow."""
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def _carrega_check_release():
    spec = importlib.util.spec_from_file_location("check_release", ROOT / "scripts" / "check_release.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _monta_raiz(tmp: str, template: str, pacote: str) -> Path:
    raiz = Path(tmp)
    (raiz / "guilda").mkdir()
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
        self.cr = _carrega_check_release()

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
            for tag in ("2.0", "v2.0.0-rc.1", "v2.0", ""):
                with self.subTest(tag=tag):
                    problemas = self.cr.check(tag, _monta_raiz_nova("2.0.0", "2.0.0"))
                    self.assertTrue(any("formato" in p for p in problemas))

    def test_template_e_pacote_divergentes_com_tag_correta(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = _monta_raiz(tmp, "2.0.0", "1.9.0")
            problemas = self.cr.check("v2.0.0", raiz)
            self.assertEqual(len(problemas), 1)
            self.assertIn("__version__", problemas[0])


def _monta_raiz_nova(template: str, pacote: str) -> Path:
    tmp = tempfile.TemporaryDirectory()
    CheckReleaseTest._tmps = getattr(CheckReleaseTest, "_tmps", [])
    CheckReleaseTest._tmps.append(tmp)
    return _monta_raiz(tmp.name, template, pacote)


class ReleaseWorkflowTest(unittest.TestCase):
    def test_release_workflow_is_gated(self):
        texto = WORKFLOW.read_text(encoding="utf-8")

        # Gatilho: somente push de tags v*.
        on = re.search(r"(?ms)^on:\n(.*?)(?=^\S)", texto).group(1)
        self.assertEqual(
            [l.strip() for l in on.splitlines() if l.strip()],
            ["push:", 'tags: ["v*"]'],
        )

        # Permissões padrão mínimas.
        self.assertRegex(texto, r"(?m)^permissions:\n  contents: read\n")

        jobs = _jobs(texto)
        self.assertEqual(set(jobs), {"verify", "build", "publish"})
        publish = jobs["publish"]
        self.assertRegex(publish, r"(?m)^    environment: pypi\s*$")
        self.assertRegex(publish, r"(?m)^    needs: build\s*$")
        self.assertRegex(publish, r"(?m)^      id-token: write\s*$")
        self.assertIn("pypa/gh-action-pypi-publish@", publish)
        self.assertRegex(jobs["build"], r"(?m)^    needs: verify\s*$")

        # Só o job que publica tem id-token; nenhum segredo ou token.
        com_id_token = [n for n, t in jobs.items() if "id-token" in t]
        com_publicacao = [n for n, t in jobs.items() if "gh-action-pypi-publish" in t]
        self.assertEqual(com_id_token, ["publish"])
        self.assertEqual(com_publicacao, ["publish"])
        self.assertNotIn("secrets.", texto)
        self.assertNotIn("password:", texto)
        # Nada que aprove o ambiente ou contorne a aprovação manual.
        self.assertNotIn("gh api", texto)
        self.assertNotIn("pending_deployments", texto)


if __name__ == "__main__":
    unittest.main()
