import json
import os
from pathlib import Path
import yaml

def _field_type(prop):
    t = prop.get('type', 'object')
    if t == 'array':
        item_t = prop.get('items', {}).get('type', 'object')
        return f"array[{item_t}]"
    return t

def main():
    repo_root = Path(__file__).resolve().parent.parent
    tk_kit_dir = repo_root / 'tk-kit'
    openapi_path = tk_kit_dir / 'openapi.yaml'
    output_dir = tk_kit_dir / 'llm'
    api_info_path = tk_kit_dir / 'api_info.json'

    if output_dir.exists():
        for p in output_dir.glob('*.json'):
            p.unlink()
    else:
        output_dir.mkdir(parents=True)

    with open(openapi_path, 'r', encoding='utf-8') as f:
        spec = yaml.safe_load(f)

    base_url = spec.get('servers', [{}])[0].get('url', '')
    endpoints = {}

    paths = spec.get('paths', {})
    for path, methods in paths.items():
        for method, info in methods.items():
            endpoint = {
                'path': path,
                'method': method.upper(),
                'summary': info.get('summary', '')
            }

            rb_schema = (
                info.get('requestBody', {})
                    .get('content', {})
                    .get('application/json', {})
                    .get('schema')
            )
            if rb_schema and 'properties' in rb_schema:
                req_fields = []
                required_list = rb_schema.get('required', [])
                for name, prop in rb_schema['properties'].items():
                    req_fields.append({
                        'name': name,
                        'description': prop.get('description', ''),
                        'type': _field_type(prop),
                        'required': 'Да' if name in required_list else 'Нет',
                        'example': json.dumps(prop['example']) if 'example' in prop else ''
                    })
                endpoint['request_fields'] = req_fields
                endpoint['response_fields'] = []
                examples = {
                    n: prop['example']
                    for n, prop in rb_schema['properties'].items()
                    if 'example' in prop
                }
                endpoint['example_request'] = json.dumps(examples, ensure_ascii=False)
                endpoint['example_response'] = ''

            file_name = f"{path.lstrip('/').replace('/', '-')}.json"
            with open(output_dir / file_name, 'w', encoding='utf-8') as f:
                json.dump(endpoint, f, ensure_ascii=False, indent=2)
            endpoints[path] = f"llm/{file_name}"

    api_info = {
        'base_url': base_url,
        'authorization': [
            'Bearer token in Authorization header',
            'token query parameter'
        ],
        'endpoints': endpoints
    }

    with open(api_info_path, 'w', encoding='utf-8') as f:
        json.dump(api_info, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
