import json
import os
from pathlib import Path
import yaml

def sanitize_filename(path: str, method: str) -> str:
    sanitized = path.strip('/').replace('/', '_').replace('{', '').replace('}', '')
    if not sanitized:
        sanitized = 'root'
    return f"{method.upper()}_{sanitized}.json"

def extract_fields(schema: dict) -> list:
    properties = schema.get('properties', {})
    required = set(schema.get('required', []))
    fields = []
    for name, prop in properties.items():
        field = {
            "name": name,
            "description": prop.get('description', ''),
            "type": prop.get('type', ''),
            "required": "Да" if name in required else "Нет",
        }
        if 'example' in prop:
            field["example"] = prop['example']
        fields.append(field)
    return fields

def get_example(content: dict):
    if not content:
        return None
    if 'example' in content:
        return content['example']
    examples = content.get('examples')
    if examples:
        first = next(iter(examples.values()))
        return first.get('value')
    return None

def main():
    root = Path(__file__).resolve().parents[1]
    spec_path = root / 'tk-kit' / 'openapi.yaml'
    index_path = root / 'tk-kit' / 'api_info.json'
    output_dir = root / 'tk-kit' / 'llm'
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    base_url = spec.get('servers', [{}])[0].get('url', '')

    authorization = []
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            try:
                existing = json.load(f)
                authorization = existing.get('authorization', [])
            except Exception:
                pass

    endpoints = []

    for path, methods in spec.get('paths', {}).items():
        for method, details in methods.items():
            if method.lower() not in {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace'}:
                continue
            summary = details.get('summary', '')
            endpoint_info = {
                "path": path,
                "method": method.upper(),
                "summary": summary,
            }
            endpoints.append(endpoint_info)

            endpoint_json = dict(endpoint_info)

            req_body = details.get('requestBody', {})
            req_content = req_body.get('content', {}).get('application/json', {})
            schema = req_content.get('schema', {})
            endpoint_json["request_fields"] = extract_fields(schema)

            resp = details.get('responses', {}).get('200') or details.get('responses', {}).get('201') or {}
            resp_content = resp.get('content', {}).get('application/json', {})
            resp_schema = resp_content.get('schema', {})
            endpoint_json["response_fields"] = extract_fields(resp_schema)

            example_request = get_example(req_content)
            if example_request is not None:
                endpoint_json["example_request"] = json.dumps(example_request, ensure_ascii=False)
            else:
                endpoint_json["example_request"] = ""

            example_response = get_example(resp_content)
            if example_response is not None:
                endpoint_json["example_response"] = json.dumps(example_response, ensure_ascii=False)
            else:
                endpoint_json["example_response"] = ""

            filename = sanitize_filename(path, method)
            with open(output_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(endpoint_json, f, ensure_ascii=False, indent=2)
                f.write("\n")

    api_info = {
        "base_url": base_url,
        "authorization": authorization,
        "endpoints": endpoints,
    }

    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(api_info, f, ensure_ascii=False, indent=2)
        f.write("\n")

if __name__ == '__main__':
    main()
