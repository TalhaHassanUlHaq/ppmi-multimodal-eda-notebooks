import json
from pathlib import Path
import pandas as pd
from io import StringIO

def extract_manifest():
    notebooks = [
        "00_dataset_overview.ipynb",
        "eda_clinical.ipynb",
        "eda_biospecimen.ipynb",
        "eda_genetics.ipynb",
        "eda_neuroimaging.ipynb",
        "eda_digital_sensors.ipynb",
        "eda_multimodal_synthesis.ipynb"
    ]

    manifest = {"notebooks": {}, "deep_tables": {}}

    for nb_name in notebooks:
        p = Path("notebooks") / nb_name if (Path("notebooks") / nb_name).exists() else Path(nb_name)
        nb = json.load(open(p, encoding="utf-8"))
        code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
        nb_outputs = sum(len(c.get("outputs", [])) for c in code_cells)
        nb_errors = sum(1 for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error")
        manifest["notebooks"][nb_name] = {
            "code_cells": len(code_cells),
            "total_outputs": nb_outputs,
            "errors": nb_errors
        }

        # Extract deep inventory table (Table 8.1 or Table 7.1)
        for cell in nb["cells"]:
            if cell.get("cell_type") != "code":
                continue
            for out in cell.get("outputs", []):
                html = out.get("data", {}).get("text/html", "")
                if isinstance(html, list):
                    html = "".join(html)
                if "Source Path" in html and "Incremental Scientific Purpose" in html:
                    dfs = pd.read_html(StringIO(html))
                    for df in dfs:
                        clean_df = df[[c for c in df.columns if not str(c).startswith("Unnamed:")]]
                        records = []
                        for _, r in clean_df.iterrows():
                            records.append({
                                "path": str(r.get("Source Path")),
                                "dims": str(r.get("Dimensions (Rows x Cols)")),
                                "grain": str(r.get("Observation Grain")),
                                "keys": str(r.get("Grain Keys")),
                                "doc": str(r.get("Documentation Source"))
                            })
                        manifest["deep_tables"][nb_name] = records

    return manifest

if __name__ == "__main__":
    m = extract_manifest()
    print("Notebook Counts:")
    for k, v in m["notebooks"].items():
        print(f"  {k}: {v['code_cells']} code cells, {v['total_outputs']} outputs, {v['errors']} errors")
    
    print("\nDeep Table Inventories:")
    for nb, rows in m["deep_tables"].items():
        print(f"\n--- {nb} ({len(rows)} sources) ---")
        for r in rows:
            print(f"  {r['path']} | {r['dims']} | keys: {r['keys']}")
