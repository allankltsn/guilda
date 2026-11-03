"""Confere o conteúdo do wheel do guilda. Pulado quando o módulo `build` não está instalado."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEM_BUILD = importlib.util.find_spec("build") is not None

# Segmentos de caminho proibidos (casamento por segmento, nunca por substring).
PROIBIDOS = ("docs", "assets", "tests", ".github", "graphify-out", ".dev", ".worktrees", "plans", "specs")


@unittest.skipUnless(TEM_BUILD, "módulo `build` não instalado")
class WheelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._tmp.cleanup)
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", cls._tmp.name, str(ROOT)],
            check=True, stdin=subprocess.DEVNULL, timeout=600,
        )
        wheels = list(Path(cls._tmp.name).glob("*.whl"))
        assert len(wheels) == 1, wheels
        with zipfile.ZipFile(wheels[0]) as z:
            cls.nomes = z.namelist()

    def test_inclui_payload_e_licenca(self):
        self.assertIn("guilda/_data/template.json", self.nomes)
        self.assertTrue(any(n.startswith("guilda/_data/core/") for n in self.nomes))
        self.assertTrue(any(n.split("/")[-1] == "LICENSE" for n in self.nomes))

    def test_nao_inclui_material_interno(self):
        for nome in self.nomes:
            segmentos = nome.split("/")
            for proibido in PROIBIDOS:
                self.assertNotIn(proibido, segmentos, nome)


if __name__ == "__main__":
    unittest.main()
