#!/usr/bin/env python3
import requests
import json

API_BASE = 'http://localhost:10001/api/v1'

# Get types
response = requests.get(f'{API_BASE}/assets/types')
types = {t['name']: t for t in response.json()}

print("Available types:")
for name in types:
    print(f"  - {name}")

# Try creating a simple hierarchy
domain = {
    'name': 'Test Domain',
    'asset_type_id': types['Domain / System of Systems']['id'],
    'description': 'Test domain',
    'status': 'active',
    'external_id': 'TEST-D1',
    'properties': {}
}

r = requests.post(f'{API_BASE}/assets', json=domain)
print(f'\nDomain created: {r.status_code}')
if r.status_code == 200:
    domain_id = r.json()['id']
    
    # Create a system under it
    system = {
        'name': 'Test System',
        'asset_type_id': types['System / Environment']['id'],
        'parent_id': domain_id,
        'description': 'Test system',
        'status': 'active',
        'external_id': 'TEST-S1',
        'properties': {}
    }
    r = requests.post(f'{API_BASE}/assets', json=system)
    print(f'System created: {r.status_code}')
    
    if r.status_code == 200:
        sys_id = r.json()['id']
        
        # Create a hardware CI
        hw = {
            'name': 'Test Equipment',
            'asset_type_id': types['Hardware CI']['id'],
            'parent_id': sys_id,
            'description': 'Test equipment',
            'status': 'active',
            'external_id': 'TEST-H1',
            'properties': {}
        }
        r = requests.post(f'{API_BASE}/assets', json=hw)
        print(f'Hardware CI created: {r.status_code}')
        if r.status_code != 200:
            print('Error:', r.text)