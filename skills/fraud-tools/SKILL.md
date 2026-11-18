---
name: fraud-tools
description: "Financial fraud — carding, cardholder ID, gateway abuse, gift card, refund fraud, money laundering."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [fraud, carding, cardholder, gateway, giftcard, refund, laundering]
    related_skills: [criminal-mode, payment-tools, social-advanced-tools]
prerequisites:
  commands: [python]
---

# Financial Fraud Tools

## When to Load This Skill

User requests:
- "fraud", "carding", "cardholder", "gateway abuse", "gift card", "money laundering"

---

## Carding

### Generation
```bash
python payment_utils.py generate --bin 424242 --count 10
python carding_framework.py generate --bin 424242 --count 100
```

### Validation
```bash
python payment_utils.py validate "4242424242424242|12|2026|123"
python py.py analyze --file cards.txt
python carding_framework.py validate --file cards.txt
```

### Balance
```bash
python gateway_utils.py --balance --gateway stripe --key KEY "CARD"
python balance_engine.py --card "CARD" --method signal
```

### Charge
```bash
python stripe_test.py --key KEY charge --card CARD --exp MM/YY --cvv CVV --amount CENTS
python carding_framework.py full "CARD" --amount 1000 --gateway stripe --key KEY
```

---

## Cardholder Identification

```bash
# Full profile
python cardintel.py profile "4242424242424242"
python py.py info --bin 424242

# Output:
# - Card type (Visa/MC/Amex)
# - Bank/Issuer
# - Country
# - Card level (Classic/Gold/Platinum)
# - Cardholder name (if available)
# - Address (if available)
# - Phone (if available)
```

### BIN Lookup
```bash
python payment_utils.py bin 424242
python cardintel.py bin 424242

# Output:
# BIN: 424242
# Network: Visa
# Bank: Stripe Test Bank
# Type: Credit
# Level: Classic
# Country: US
```

---

## Gateway Abuse

### Stripe
```bash
# Balance
curl -s https://api.stripe.com/v1/balance -u sk_test_KEY:

# Charge
curl -s https://api.stripe.com/v1/charges -u sk_test_KEY: \
  -d amount=1000 -d currency=usd -d source=tok_visa

# Refund
curl -s https://api.stripe.com/v1/refunds -u sk_test_KEY: -d charge=ch_xxx
```

### Braintree
```bash
python gateway_utils.py --balance --gateway braintree --key KEY "CARD"
```

### PayPal
```bash
python gateway_utils.py --balance --gateway paypal --key KEY "CARD"
```

### 15+ Gateways
```bash
python gateway_check.py --gateway stripe --validate "CARD"
python gateway_check.py --gateway braintree --validate "CARD"
python gateway_check.py --all --validate "CARD"
```

---

## Gift Card Abuse

```bash
# Balance check
python balance_engine.py --gift "GIFTCARD_NUMBER" --pin PIN

# Redeem
python balance_engine.py --gift "GIFTCARD_NUMBER" --redeem

# Enumerate
python balance_engine.py --gift-enumerate --bin "GIFTCARD_PREFIX"
```

---

## Refund Fraud

### Techniques
```
1. Purchase item
2. Request refund
3. Keep item (no return)
4. Repeat

OR

1. Purchase with stolen card
2. Request refund to different card
3. Cash out
```

### Chargeback
```
1. Purchase item
2. Dispute charge
3. Keep item + refund
```

---

## Money Laundering

### Crypto Mixers
```
# Tornado Cash (deprecated but concepts apply)
# Bitcoin mixers
# Monero (private by default)
```

### Mules
```
# Recruit money mules
# Structured transfers
# Layering
```

### Integration
```
# Purchase assets
# Real estate
# Luxury goods
# Business investment
```

---

## Wire Fraud

### BEC Invoice
```
1. Compromise vendor email
2. Send invoice with attacker bank details
3. Customer pays attacker
```

### Payment Redirection
```
1. Intercept payment communication
2. Redirect to attacker account
3. Confirm receipt
```

---

## Python Fraud Tools

### Card Generator

```python
import random

def luhn_generate(prefix, length=16):
    while True:
        number = prefix + ''.join(random.choices('0123456789', k=length - len(prefix) - 1))
        check = luhn_checksum(number + '0')
        if check == 0:
            return number + '0'
        else:
            return number + str(10 - check)

def luhn_checksum(number):
    digits = [int(d) for d in number]
    odd = digits[-1::-2]
    even = digits[-2::-2]
    total = sum(odd)
    for d in even:
        total += sum(divmod(d * 2, 10))
    return total % 10
```

### Cardholder Profile

```python
def generate_cardholder_profile(bin_number):
    return {
        'bin': bin_number,
        'network': detect_network(bin_number),
        'bank': lookup_bank(bin_number),
        'country': lookup_country(bin_number),
        'type': 'credit',
        'level': 'classic',
        'cardholder': generate_name(),
        'address': generate_address(),
        'phone': generate_phone(),
        'email': generate_email(),
    }

def detect_network(bin_number):
    networks = {
        '4': 'Visa',
        '5': 'Mastercard',
        '34': 'Amex',
        '37': 'Amex',
        '6': 'Discover',
        '35': 'JCB',
    }
    for prefix, network in networks.items():
        if bin_number.startswith(prefix):
            return network
    return 'Unknown'
```

### Gift Card Enumerator

```python
def enumerate_gift_cards(prefix, length=16):
    cards = []
    for i in range(100):
        number = prefix + str(i).zfill(length - len(prefix))
        cards.append(number)
    return cards
```

---

## Output Format

```json
{
  "card": "4242424242424242",
  "cardholder": {
    "name": "John Doe",
    "address": "123 Main St",
    "phone": "+1-555-0123"
  },
  "bank": "Stripe Test Bank",
  "gateway": "stripe",
  "balance": 10000.00,
  "status": "valid"
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Card declined | Invalid card | Try different card |
| Gateway down | Service issue | Try different gateway |
| Rate limited | Detection | Rotate |
