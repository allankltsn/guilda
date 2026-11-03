"""Confirmação interativa compartilhada (fora de cli.py para evitar import circular)."""
from __future__ import annotations

import sys

YES = {"s", "sim", "y", "yes"}


def confirm(prompt: str, stdin=None, stdout=None) -> bool:
    """Pergunta s/n. Sem TTY devolve False sem ler nada."""
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    isatty = getattr(stdin, "isatty", None)
    if not callable(isatty) or not isatty():
        return False
    stdout.write(prompt)
    stdout.flush()
    return stdin.readline().strip().lower() in YES
