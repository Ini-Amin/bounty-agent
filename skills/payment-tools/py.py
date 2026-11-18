#!/usr/bin/env python3
"""
py.py — Main Payment Tools Wrapper
Usage:
    python py.py analyze --file cards.txt
    python py.py info --bin 424242
    python py.py validate --card "4242424392025559|01/27|063"
"""

import sys
import json
import argparse
from payment_utils import analyze_file, lookup_bin, parse_card_line, luhn_check, detect_network


def main():
    parser = argparse.ArgumentParser(description="Payment Tools — Main Wrapper")
    subparsers = parser.add_subparsers(dest="command")
    
    # Analyze file
    analyze_parser = subparsers.add_parser("analyze", help="Analyze cards from file")
    analyze_parser.add_argument("--file", required=True, help="Path to cards file")
    
    # BIN info
    info_parser = subparsers.add_parser("info", help="Get BIN/card information")
    info_parser.add_argument("--bin", help="BIN number (6 digits)")
    info_parser.add_argument("--card", help="Full card: NUM|MM|YY|CVV")
    
    # Validate
    val_parser = subparsers.add_parser("validate", help="Validate card")
    val_parser.add_argument("card", help="Card: NUM|MM|YY|CVV")
    
    # Process (full pipeline)
    proc_parser = subparsers.add_parser("process", help="Process cards with amount")
    proc_parser.add_argument("--file", required=True, help="Path to cards file")
    proc_parser.add_argument("--amount", type=float, default=99.99, help="Amount to charge")
    proc_parser.add_argument("--gateway", default="stripe", help="Payment gateway")
    
    parser.add_argument("--json", action="store_true", help="JSON output")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        result = analyze_file(args.file)
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n{'='*60}")
            print(f"  CARD FILE ANALYSIS — {args.file}")
            print(f"{'='*60}")
            print(f"  Total Cards:      {result.get('total', 0)}")
            print(f"  Valid Luhn:       {result.get('valid_luhn', 0)}")
            print(f"  Invalid Luhn:     {result.get('invalid_luhn', 0)}")
            print(f"  Active (not exp): {result.get('active', 0)}")
            print(f"  Expired:          {result.get('expired', 0)}")
            print(f"  Networks:         {result.get('networks', {})}")
            print(f"{'='*60}")
            
            for i, card in enumerate(result.get("cards", []), 1):
                luhn_icon = "✓" if card["luhn_valid"] else "✗"
                exp_status = "ACTIVE" if not card["expiry"]["expired"] else "EXPIRED"
                print(f"\n  [{i}] {card['masked']}")
                print(f"      Network: {card['network']}")
                print(f"      Luhn:    {luhn_icon} ({card['luhn_msg']})")
                print(f"      Expiry:  {card['month']}/{card['year']} — {exp_status}")
                if card["bin_info"]:
                    bi = card["bin_info"]
                    print(f"      Bank:    {bi['bank']}")
                    print(f"      Country: {bi['country']}")
                    print(f"      Level:   {bi['level']}")
    
    elif args.command == "info":
        if args.bin:
            bin_info = lookup_bin(args.bin)
            if bin_info:
                result = {"bin": args.bin, **bin_info}
            else:
                result = {"bin": args.bin, "status": "NOT_FOUND"}
        elif args.card:
            card = parse_card_line(args.card)
            if card:
                result = card
            else:
                result = {"error": "Invalid format. Use: NUM|MM|YY|CVV"}
        else:
            parser.print_help()
            return
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            for k, v in result.items():
                if isinstance(v, dict):
                    print(f"\n  {k}:")
                    for kk, vv in v.items():
                        print(f"    {kk}: {vv}")
                elif isinstance(v, list):
                    print(f"\n  {k}: {', '.join(str(x) for x in v)}")
                else:
                    print(f"  {k}: {v}")
    
    elif args.command == "validate":
        card = parse_card_line(args.card)
        if card:
            result = {
                "card": card["masked"],
                "network": card["network"],
                "luhn_valid": card["luhn_valid"],
                "luhn_msg": card["luhn_msg"],
                "expiry_status": card["expiry"]["status"],
                "bin": card["bin"]
            }
        else:
            result = {"error": "Invalid format"}
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            luhn_icon = "✓ VALID" if result.get("luhn_valid") else "✗ INVALID"
            print(f"\n  CARD VALIDATION")
            print(f"  {'='*40}")
            print(f"  Card:    {result.get('card', 'N/A')}")
            print(f"  Network: {result.get('network', 'Unknown')}")
            print(f"  Luhn:    {luhn_icon}")
            print(f"  Expiry:  {result.get('expiry_status', 'Unknown')}")
            print(f"  BIN:     {result.get('bin', 'N/A')}")
    
    elif args.command == "process":
        result = analyze_file(args.file)
        
        process_result = {
            "gateway": args.gateway,
            "amount": args.amount,
            "cards_found": result.get("total", 0),
            "valid_cards": result.get("valid_luhn", 0),
            "active_cards": result.get("active", 0),
            "networks": result.get("networks", {}),
            "note": "Stripe/test keys required for actual processing"
        }
        
        if args.json:
            print(json.dumps(process_result, indent=2, default=str))
        else:
            print(f"\n  PAYMENT PROCESSING")
            print(f"  {'='*40}")
            print(f"  Gateway:    {args.gateway}")
            print(f"  Amount:     ${args.amount}")
            print(f"  Cards:      {process_result['valid_cards']} valid / {process_result['cards_found']} total")
            print(f"  Active:     {process_result['active_cards']}")
            print(f"  Networks:   {process_result['networks']}")
            print(f"  {'='*40}")
            print(f"  ℹ  To charge, use: python stripe_test.py --key KEY charge ...")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
