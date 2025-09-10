import json
import re
from pathlib import Path
from typing import Any, Dict

import requests
import yaml
from bs4 import BeautifulSoup

BASE_URL = "https://tk-kit.ru"
DOC_ROOT = f"{BASE_URL}/developers/api-doc"

TYPE_MAP = {
    "строка": "string",
    "string": "string",
    "integer": "integer",
    "int": "integer",
    "boolean": "boolean",
    "bool": "boolean",
    "массив": "array",
}


def map_type(text: str) -> str:
    text = text.lower()
    for key, val in TYPE_MAP.items():
        if key in text:
            return val
    return "string"


def parse_example(code_tag) -> Any:
    if not code_tag:
        return None
    try:
        return json.loads(code_tag.get_text())
    except Exception:
        return None


def schema_from_example(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return {
            "type": "object",
            "properties": {k: schema_from_example(v) for k, v in value.items()},
        }
    if isinstance(value, list):
        if value:
            return {"type": "array", "items": schema_from_example(value[0])}
        return {"type": "array"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    return {"type": "string"}


def update_spec(spec_path: Path):
    with spec_path.open("r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    paths = spec.get("paths", {})

    for path, methods in paths.items():
        doc_url = DOC_ROOT + path
        try:
            resp = requests.get(doc_url, timeout=20, verify=False)
            resp.raise_for_status()
        except Exception:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")

        for method, info in list(methods.items()):
            method_lower = method.lower()

            # Request fields
            h4_req = soup.find("h4", string=lambda s: s and "Поля запроса" in s)
            props = {}
            required = []
            if h4_req:
                table = h4_req.find_next("table")
                if table:
                    for row in table.find_all("tr"):
                        cells = row.find_all("td")
                        if len(cells) < 5:
                            continue
                        name = cells[0].get_text(strip=True)
                        desc = cells[1].get_text(" ", strip=True)
                        typ = cells[2].get_text(" ", strip=True)
                        required_flag = "Да" in cells[3].get_text()
                        ex_val = cells[4].get_text(strip=True)
                        schema = {"type": map_type(typ)}
                        if desc:
                            schema["description"] = desc
                        if ex_val:
                            schema["example"] = ex_val
                        props[name] = schema
                        if required_flag:
                            required.append(name)

            h4_req_ex = soup.find("h4", string=lambda s: s and "Пример запроса" in s)
            example_req = parse_example(h4_req_ex.find_next("code")) if h4_req_ex else None
            if example_req and isinstance(example_req, dict):
                for k, v in example_req.items():
                    prop = props.setdefault(k, {})
                    prop.setdefault("type", schema_from_example(v).get("type", "string"))
                    prop["example"] = v
            if props:
                schema = {"type": "object", "properties": props}
                if required:
                    schema["required"] = required
                if method_lower in {"get", "delete"}:
                    parameters = []
                    for name, prop in props.items():
                        param = {
                            "name": name,
                            "in": "query",
                            "schema": {"type": prop.get("type", "string")},
                        }
                        if prop.get("description"):
                            param["description"] = prop["description"]
                        if prop.get("example") is not None:
                            param["example"] = prop["example"]
                        if required and name in required:
                            param["required"] = True
                        parameters.append(param)
                    info["parameters"] = parameters
                else:
                    info["requestBody"] = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": schema,
                            }
                        },
                    }
                    if example_req:
                        info["requestBody"]["content"]["application/json"]["example"] = example_req

            # Example response
            h4_resp_ex = soup.find("h4", string=lambda s: s and ("Пример ответа" in s or "Ответ сервера" in s))
            example_resp = parse_example(h4_resp_ex.find_next("code")) if h4_resp_ex else None
            if example_resp is not None:
                responses = info.setdefault("responses", {})
                responses["200"] = {
                    "description": "",
                    "content": {
                        "application/json": {
                            "example": example_resp,
                            "schema": schema_from_example(example_resp),
                        }
                    },
                }

    with spec_path.open("w", encoding="utf-8") as f:
        yaml.dump(spec, f, allow_unicode=True, sort_keys=False)


def main():
    root = Path(__file__).resolve().parents[1]
    spec_path = root / "tk-kit" / "openapi.yaml"
    update_spec(spec_path)


if __name__ == "__main__":
    main()
