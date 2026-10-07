"""Download the pinned annotation table and verify its SHA-256."""

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen


def main():
    directory = Path(__file__).resolve().parent / "data/annotations"
    metadata_path = (
        directory / "Supplemental_file1_neuron_annotations.source.json"
    )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    output = directory / "Supplemental_file1_neuron_annotations.tsv"

    if output.exists():
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        if digest == metadata["sha256"]:
            print("OK: lokalna tabela ma poprawną sumę SHA-256.")
            return
        raise SystemExit(
            "Lokalna tabela ma inną sumę SHA-256. Nie nadpisano pliku."
        )

    with urlopen(metadata["source_url"], timeout=60) as response:
        content = response.read()

    if hashlib.sha256(content).hexdigest() != metadata["sha256"]:
        raise SystemExit("Niezgodna suma SHA-256. Nie zapisano tabeli.")

    with output.open("xb") as file:
        file.write(content)

    print("OK: pobrano i zweryfikowano:", output)


if __name__ == "__main__":
    main()
