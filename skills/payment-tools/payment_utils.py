#!/usr/bin/env python3
"""
payment_utils.py — BIN Lookup + Card Utilities
Usage:
    python payment_utils.py bin <BIN_NUMBER>
    python payment_utils.py luhn <CARD_NUMBER>
    python payment_utils.py info <CARD_NUMBER>
"""

import sys
import json
import argparse
from typing import Dict, Optional, Tuple

# BIN Database (major issuers)
BIN_DATABASE = {
    "424242": {"bank": "Stripe Test Bank", "country": "US", "type": "Visa", "level": "Classic", "prepaid": False},
    "411111": {"bank": "Stripe Test Bank", "country": "US", "type": "Visa", "level": "Classic", "prepaid": False},
    "529933": {"bank": "MASTER RED EUROPA S.L.", "country": "ES", "type": "Mastercard", "level": "Platinum", "prepaid": False},
    "555555": {"bank": "Mastercard Test", "country": "US", "type": "Mastercard", "level": "Platinum", "prepaid": False},
    "378282": {"bank": "American Express", "country": "US", "type": "Amex", "level": "Gold", "prepaid": False},
    "371449": {"bank": "American Express", "country": "US", "type": "Amex", "level": "Gold", "prepaid": False},
    "601111": {"bank": "Discover Test", "country": "US", "type": "Discover", "level": "Classic", "prepaid": False},
    "356600": {"bank": "JCB Test", "country": "JP", "type": "JCB", "level": "Classic", "prepaid": False},
    "400000": {"bank": "Visa Test", "country": "US", "type": "Visa", "level": "Classic", "prepaid": False},
    "400005": {"bank": "Visa Debit Test", "country": "US", "type": "Visa", "level": "Debit", "prepaid": False},
    "510000": {"bank": "Mastercard Test", "country": "US", "type": "Mastercard", "level": "Classic", "prepaid": False},
    "520000": {"bank": "Mastercard Test", "country": "US", "type": "Mastercard", "level": "Platinum", "prepaid": False},
    "540000": {"bank": "Mastercard Test", "country": "US", "type": "Mastercard", "level": "Platinum", "prepaid": False},
    "601100": {"bank": "Discover Test", "country": "US", "type": "Discover", "level": "Classic", "prepaid": False},
    "650000": {"bank": "Discover Test", "country": "US", "type": "Discover", "level": "Classic", "prepaid": False},
}

# Card Network Detection
CARD_NETWORKS = {
    "Visa": {"prefixes": ["4"], "lengths": [13, 16, 19]},
    "Mastercard": {"prefixes": ["51", "52", "53", "54", "55", "2221", "2222", "2223", "2224", "2225", "2226", "2227", "2228", "2229", "223", "224", "225", "226", "227", "228", "229", "23", "24", "25", "26", "270", "271", "2720"], "lengths": [16]},
    "Amex": {"prefixes": ["34", "37"], "lengths": [15]},
    "Discover": {"prefixes": ["6011", "622", "644", "645", "646", "647", "648", "649", "65"], "lengths": [16, 19]},
    "JCB": {"prefixes": ["3528", "3529", "353", "354", "355", "356", "357", "358"], "lengths": [15, 16]},
    "Diners": {"prefixes": ["300", "301", "302", "303", "304", "305", "36", "38", "39"], "lengths": [14]},
    "UnionPay": {"prefixes": ["62"], "lengths": [16, 17, 18, 19]},
}


def luhn_check(card_number: str) -> Tuple[bool, str]:
    """Validate card number using Luhn algorithm."""
    card_number = card_number.replace(" ", "").replace("-", "")
    
    if not card_number.isdigit():
        return False, "Card number contains non-digit characters"
    
    if len(card_number) < 13 or len(card_number) > 19:
        return False, f"Invalid length: {len(card_number)} (expected 13-19)"
    
    # Luhn algorithm
    digits = [int(d) for d in card_number]
    digits.reverse()
    
    total = 0
    for i, d in enumerate(digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    
    if total % 10 == 0:
        return True, "Valid"
    else:
        return False, f"Invalid checksum (expected last digit to make sum divisible by 10)"


def detect_network(card_number: str) -> str:
    """Detect card network from number."""
    card_number = card_number.replace(" ", "").replace("-", "")
    
    for network, info in CARD_NETWORKS.items():
        for prefix in info["prefixes"]:
            if card_number.startswith(prefix):
                if len(card_number) in info["lengths"]:
                    return network
    return "Unknown"


def lookup_bin(bin_number: str) -> Optional[Dict]:
    """Lookup BIN in database."""
    return BIN_DATABASE.get(bin_number, None)


def get_expiry_info(month: str, year: str) -> Dict:
    """Check expiry status."""
    from datetime import datetime
    
    try:
        m = int(month)
        y = int(year)
        if y < 100:
            y += 2000
        
        exp_date = datetime(y, m, 1)
        now = datetime.now()
        
        if exp_date > now:
            days_remaining = (exp_date - now).days
            return {"valid": True, "expired": False, "days_remaining": days_remaining, "status": "ACTIVE"}
        else:
            return {"valid": True, "expired": True, "days_remaining": 0, "status": "EXPIRED"}
    except:
        return {"valid": False, "expired": None, "days_remaining": 0, "status": "INVALID_DATE"}


def parse_card_line(line: str) -> Optional[Dict]:
    """Parse card line in format NUM|MM|YY|CVV or NUM|MM/YY|CVV."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    
    parts = line.split("|")
    
    # Handle NUM|MM/YY|CVV format (3 parts)
    if len(parts) == 3:
        number, expiry, cvv = parts
        number = number.strip()
        expiry = expiry.strip()
        cvv = cvv.strip()
        
        # Split MM/YY
        exp_parts = expiry.split("/")
        if len(exp_parts) == 2:
            month = exp_parts[0].strip()
            year = exp_parts[1].strip()
        else:
            return None
    # Handle NUM|MM|YY|CVV format (4 parts)
    elif len(parts) == 4:
        number, month, year, cvv = parts
        number = number.strip()
        month = month.strip()
        year = year.strip()
        cvv = cvv.strip()
    else:
        return None
    
    # Validate
    luhn_valid, luhn_msg = luhn_check(number)
    network = detect_network(number)
    bin_num = number[:6]
    bin_info = lookup_bin(bin_num)
    expiry = get_expiry_info(month, year)
    
    # Mask card number
    masked = number[:6] + "*" * (len(number) - 10) + number[-4:] if len(number) >= 10 else number
    
    return {
        "number": number,
        "masked": masked,
        "cvv": cvv,
        "month": month,
        "year": year,
        "network": network,
        "luhn_valid": luhn_valid,
        "luhn_msg": luhn_msg,
        "bin": bin_num,
        "bin_info": bin_info,
        "expiry": expiry,
    }


def analyze_file(filepath: str) -> Dict:
    """Analyze all cards in a file."""
    results = {
        "total": 0,
        "valid_luhn": 0,
        "invalid_luhn": 0,
        "expired": 0,
        "active": 0,
        "networks": {},
        "cards": []
    }
    
    try:
        with open(filepath, "r") as f:
            for line in f:
                card = parse_card_line(line)
                if card is None:
                    continue
                
                results["total"] += 1
                results["cards"].append(card)
                
                if card["luhn_valid"]:
                    results["valid_luhn"] += 1
                else:
                    results["invalid_luhn"] += 1
                
                if card["expiry"]["expired"]:
                    results["expired"] += 1
                elif card["expiry"]["valid"]:
                    results["active"] += 1
                
                net = card["network"]
                results["networks"][net] = results["networks"].get(net, 0) + 1
    except FileNotFoundError:
        return {"error": f"File not found: {filepath}"}
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Payment Utilities — BIN Lookup & Card Validation")
    subparsers = parser.add_subparsers(dest="command")
    
    # BIN lookup
    bin_parser = subparsers.add_parser("bin", help="Lookup BIN information")
    bin_parser.add_argument("number", help="BIN number (first 6 digits)")
    
    # Luhn check
    luhn_parser = subparsers.add_parser("luhn", help="Validate card with Luhn algorithm")
    luhn_parser.add_argument("number", help="Card number")
    
    # Card info
    info_parser = subparsers.add_parser("info", help="Full card info")
    info_parser.add_argument("card", help="Card in format NUM|MM|YY|CVV")
    
    # Analyze file
    file_parser = subparsers.add_parser("file", help="Analyze cards from file")
    file_parser.add_argument("filepath", help="Path to cards file")
    
    # JSON output flag
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if args.command == "bin":
        bin_info = lookup_bin(args.number)
        if bin_info:
            output = {"bin": args.number, **bin_info}
        else:
            output = {"bin": args.number, "status": "NOT_FOUND", "message": "BIN not in local database"}
        
    elif args.command == "luhn":
        valid, msg = luhn_check(args.number)
        output = {"number": args.number, "valid": valid, "message": msg}
        
    elif args.command == "info":
        card = parse_card_line(args.card)
        if card:
            output = card
        else:
            output = {"error": "Invalid format. Use: NUM|MM|YY|CVV"}
        
    elif args.command == "file":
        output = analyze_file(args.filepath)
    
    else:
        parser.print_help()
        return
    
    if args.json:
        print(json.dumps(output, indent=2, default=str))
    else:
        if "cards" in output:
            # File analysis output
            print(f"\n{'='*60}")
            print(f"  CARD FILE ANALYSIS")
            print(f"{'='*60}")
            print(f"  Total Cards:      {output['total']}")
            print(f"  Valid Luhn:       {output['valid_luhn']}")
            print(f"  Invalid Luhn:     {output['invalid_luhn']}")
            print(f"  Active (not exp): {output['active']}")
            print(f"  Expired:          {output['expired']}")
            print(f"  Networks:         {output['networks']}")
            print(f"{'='*60}")
            
            for i, card in enumerate(output["cards"], 1):
                status = "✓" if card["luhn_valid"] else "✗"
                exp = "ACTIVE" if not card["expiry"]["expired"] else "EXPIRED"
                print(f"\n  [{i}] {card['masked']}")
                print(f"      Network: {card['network']} | Luhn: {status} ({card['luhn_msg']})")
                print(f"      Expiry: {card['month']}/{card['year']} — {exp}")
                if card["bin_info"]:
                    bi = card["bin_info"]
                    print(f"      Bank: {bi['bank']} | Country: {bi['country']} | Level: {bi['level']}")
        else:
            # Single card output
            for k, v in output.items():
                if isinstance(v, dict):
                    print(f"\n  {k.upper()}:")
                    for kk, vv in v.items():
                        print(f"    {kk}: {vv}")
                else:
                    print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
