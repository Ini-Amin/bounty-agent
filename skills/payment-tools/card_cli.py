#!/usr/bin/env python3
"""
card_cli.py — Card Validation CLI
Usage:
    python card_cli.py validate "NUM|MM|YY|CVV"
    python card_cli.py validate --file cards.txt
    python card_cli.py generate --bin 424242 --count 5
"""

import sys
import json
import random
import argparse
from typing import List, Dict

# Import from payment_utils
from payment_utils import luhn_check, detect_network, lookup_bin, get_expiry_info, parse_card_line


def validate_card(card_string: str) -> Dict:
    """Validate a single card string."""
    card = parse_card_line(card_string)
    if card:
        return {
            "card": card["masked"],
            "network": card["network"],
            "luhn_valid": card["luhn_valid"],
            "luhn_msg": card["luhn_msg"],
            "expiry_status": card["expiry"]["status"],
            "bin": card["bin"],
            "bin_info": card["bin_info"]
        }
    return {"error": "Invalid format. Use: NUM|MM|YY|CVV"}


def validate_file(filepath: str) -> Dict:
    """Validate all cards in a file."""
    results = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "expired": 0,
        "cards": []
    }
    
    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                card = parse_card_line(line)
                if card:
                    results["total"] += 1
                    results["cards"].append({
                        "number": card["masked"],
                        "network": card["network"],
                        "luhn": card["luhn_valid"],
                        "expired": card["expiry"]["expired"]
                    })
                    
                    if card["luhn_valid"]:
                        results["valid"] += 1
                    else:
                        results["invalid"] += 1
                    
                    if card["expiry"]["expired"]:
                        results["expired"] += 1
    except FileNotFoundError:
        return {"error": f"File not found: {filepath}"}
    
    return results


def generate_luhn(number: str) -> str:
    """Generate Luhn check digit for partial number."""
    digits = [int(d) for d in number]
    
    # Calculate sum
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    
    # Find check digit
    check = (10 - (total % 10)) % 10
    return str(check)


def generate_card(bin_prefix: str, count: int = 1) -> List[str]:
    """Generate random cards with valid Luhn."""
    cards = []
    
    for _ in range(count):
        # Generate random digits (need 15 total for Visa, 16 for MC)
        if bin_prefix.startswith("4"):
            # Visa: 16 digits
            random_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            partial = bin_prefix + random_digits
            check_digit = generate_luhn(partial)
            card_number = partial + check_digit
        else:
            # Mastercard: 16 digits
            random_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            partial = bin_prefix + random_digits
            check_digit = generate_luhn(partial)
            card_number = partial + check_digit
        
        # Generate random expiry (1-24 months from now)
        from datetime import datetime, timedelta
        future_date = datetime.now() + timedelta(days=random.randint(30, 720))
        month = f"{future_date.month:02d}"
        year = str(future_date.year)[2:]
        
        # Generate random CVV
        cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])
        
        cards.append(f"{card_number}|{month}|{year}|{cvv}")
    
    return cards


def main():
    parser = argparse.ArgumentParser(description="Card Validation CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Validate single card
    val_parser = subparsers.add_parser("validate", help="Validate a card")
    val_parser.add_argument("card", nargs="?", help="Card: NUM|MM|YY|CVV")
    val_parser.add_argument("--file", help="Validate cards from file")
    
    # Generate cards
    gen_parser = subparsers.add_parser("generate", help="Generate random cards")
    gen_parser.add_argument("--bin", required=True, help="BIN prefix (6 digits)")
    gen_parser.add_argument("--count", type=int, default=5, help="Number of cards to generate")
    gen_parser.add_argument("--output", help="Output file path")
    
    parser.add_argument("--json", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    if args.command == "validate":
        if args.file:
            result = validate_file(args.file)
        elif args.card:
            result = validate_card(args.card)
        else:
            parser.print_help()
            return
    elif args.command == "generate":
        cards = generate_card(args.bin, args.count)
        result = {
            "bin": args.bin,
            "count": len(cards),
            "cards": cards
        }
        
        if args.output:
            with open(args.output, "w") as f:
                for card in cards:
                    f.write(card + "\n")
            result["saved_to"] = args.output
    else:
        parser.print_help()
        return
    
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        if "cards" in result and isinstance(result["cards"], list):
            if "luhn" in result["cards"][0] if result["cards"] else False:
                # Validation output
                print(f"\n  VALIDATION RESULTS")
                print(f"  {'='*50}")
                print(f"  Total: {result['total']}")
                print(f"  Valid Luhn: {result['valid']}")
                print(f"  Invalid Luhn: {result['invalid']}")
                print(f"  Expired: {result['expired']}")
                print(f"  {'='*50}")
                
                for card in result["cards"]:
                    status = "✓" if card["luhn"] else "✗"
                    exp = "EXP" if card["expired"] else "OK"
                    print(f"  {status} {card['number']} | {card['network']} | {exp}")
            else:
                # Generation output
                print(f"\n  GENERATED CARDS")
                print(f"  {'='*50}")
                print(f"  BIN: {result['bin']}")
                print(f"  Count: {result['count']}")
                print(f"  {'='*50}")
                for card in result["cards"]:
                    print(f"  {card}")
                if "saved_to" in result:
                    print(f"\n  Saved to: {result['saved_to']}")
        else:
            for k, v in result.items():
                print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
