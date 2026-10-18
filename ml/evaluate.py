from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
if __name__=="__main__":
    print(json.dumps(json.loads((ROOT/"reports"/"evaluation_results.json").read_text()),indent=2))
