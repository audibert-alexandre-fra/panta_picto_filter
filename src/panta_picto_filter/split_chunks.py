import json
import os
from pathlib import Path

CHUNK_SIZE = 40_000
INPUT_DIR = Path(__file__).parent / "filtered_class"
OUTPUT_DIR = Path(__file__).parent / "chunks_40000"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    for path in sorted(INPUT_DIR.glob("*filtered_class.json")):
        base_name = path.name.replace("filtered_class.json", "").rstrip("_")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"{path.name}: {len(data)} elements, {len(data) // CHUNK_SIZE + 1} chunk(s)")

        for i in range(0, len(data), CHUNK_SIZE):
            chunk = data[i : i + CHUNK_SIZE]
            chunk_name = f"{base_name}_chunk_{i // CHUNK_SIZE}.json"
            with open(OUTPUT_DIR / chunk_name, "w", encoding="utf-8") as f:
                json.dump(chunk, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
