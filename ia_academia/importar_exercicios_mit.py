"""Importação opcional do dataset MIT via arquivo local ou GitHub (apenas textos).

Uso, dentro de ia_academia/:
    python importar_exercicios_mit.py
    python importar_exercicios_mit.py --arquivo C:\\Downloads\\exercises.json

Não baixa nem salva imagens, GIFs, paths de mídia nem traduções AGPL do openGym.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

URL_BASE = "https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/main"
DATA_BASE = Path(__file__).resolve().parent / "dados"
CAMPOS = ("id", "name", "category", "target", "equipment", "secondary_muscles")
LIMITE_BYTES = 35 * 1024 * 1024


def baixar(caminho: str) -> bytes:
    req = Request(URL_BASE + "/" + caminho, headers={"User-Agent": "FitFATEC-licensed-metadata-importer"})
    with urlopen(req, timeout=45) as response:
        data = response.read(LIMITE_BYTES + 1)
    if len(data) > LIMITE_BYTES:
        raise ValueError("Download excedeu o limite permitido")
    return data


def extrair_metadados(dados) -> list[dict]:
    if not isinstance(dados, list):
        raise ValueError("Formato inválido: esperado lista JSON")
    resultado = []
    usados = set()
    for item in dados:
        if not isinstance(item, dict):
            continue
        if not all(isinstance(item.get(k), str) and item[k].strip()
                   for k in ("id", "name", "category", "target", "equipment")):
            continue
        id_ = item["id"]
        if id_ in usados:
            continue
        usados.add(id_)
        # Lista branca: não incluir nada de mídia, créditos de mídia,
        # instruções, traduções ou URLs de terceiros.
        meta = {k: " ".join(item[k].split())[:160] for k in CAMPOS[:-1]}
        secund = item.get("secondary_muscles", [])
        meta["secondary_muscles"] = [s for s in secund if isinstance(s, str)] if isinstance(secund, list) else []
        resultado.append(meta)
    if len(resultado) < 100:
        raise ValueError("Foram encontrados poucos exercícios; arquivo inesperado ou incompleto")
    return resultado


def importar(dados: bytes, licença: bytes | None = None, aviso: bytes | None = None):
    dataset = json.loads(dados.decode("utf-8-sig"))
    res = extrair_metadados(dataset)
    DATA_BASE.mkdir(parents=True, exist_ok=True)
    destino = DATA_BASE / "exercicios_mit.json"
    destino.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if licença:
        (DATA_BASE / "EXERCISES_DATASET_LICENSE.txt").write_bytes(licença)
    if aviso:
        (DATA_BASE / "EXERCISES_DATASET_NOTICE.md").write_bytes(aviso)
    return len(res), destino


def main():
    parser = argparse.ArgumentParser(description="Importar metadados MIT de exercícios, SEM mídia")
    parser.add_argument("--arquivo", help="JSON baixado manualmente no GitHub, se preferir")
    parser.add_argument("--licenca", help="LICENSE da fonte, se estiver sem acesso ao GitHub")
    parser.add_argument("--aviso", help="NOTICE.md da fonte, se estiver sem acesso ao GitHub")
    args = parser.parse_args()
    print("Importando somente metadados e nomes de exercícios (sem imagens/GIFs).")
    dados = Path(args.arquivo).read_bytes() if args.arquivo else baixar("data/exercises.json")
    # Os dois avisos devem ser guardados junto com os dados usados.
    try:
        licença = Path(args.licenca).read_bytes() if args.licenca else baixar("LICENSE")
        aviso = Path(args.aviso).read_bytes() if args.aviso else baixar("NOTICE.md")
    except Exception as e:
        raise SystemExit("Faltam avisos de licença: baixe LICENSE e NOTICE.md "
                         "da mesma fonte, ou forneça --licenca e --aviso. "
                         f"Detalhes: {type(e).__name__}") from e
    if not licença or not aviso:
        raise SystemExit("Aviso de licença vazio: não foi possível importar com atribuição adequada.")
    n, destino = importar(dados, licença, aviso)
    print(f"Importados: {n} exercícios. Arquivo: {destino}")
    print("Reinicie `python servidor.py` para a Kiara usar a biblioteca ampliada.")


if __name__ == "__main__":
    main()
