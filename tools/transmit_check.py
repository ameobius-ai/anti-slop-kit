import json
import re
import sys

def extract_numbers(text):
    hex_nums = set(re.findall(r'0x[0-9a-fA-F]+', text, re.IGNORECASE))
    dec_nums = set(re.findall(r'\b\d+(?:\.\d+)?\b', text))
    return hex_nums | dec_nums

def extract_identifiers(text):
    words = re.findall(r'\b[A-Za-z0-9_]+\b', text)
    ids = set()
    for w in words:
        if '_' in w and len(w) > 2:
            ids.add(w)
        elif re.match(r'^[A-Z][a-z]+[A-Z]', w): # camelCase
            ids.add(w)
        elif re.match(r'^[A-Z][A-Z0-9_]{2,}$', w): # UPPER_CASE
            ids.add(w)
    return ids

def extract_constraints(text):
    constraints = set()
    bounds = re.findall(r'[<>=!]+\s*\d+(?:\.\d+)?', text)
    constraints.update(bounds)
    modals = re.findall(r'\b(?:must|shall|require[sd]?|mandatory|never|always)\b', text, re.IGNORECASE)
    constraints.update(modals)
    return constraints

def transmit_check(original, rewritten):
    o_nums = extract_numbers(original)
    r_nums = extract_numbers(rewritten)
    
    o_ids = extract_identifiers(original)
    r_ids = extract_identifiers(rewritten)
    
    o_cons = extract_constraints(original)
    r_cons = extract_constraints(rewritten)
    
    lost_nums = o_nums - r_nums
    lost_ids = o_ids - r_ids
    lost_cons = o_cons - r_cons
    
    total_facts = len(o_nums) + len(o_ids) + len(o_cons)
    lost_facts = len(lost_nums) + len(lost_ids) + len(lost_cons)
    
    fidelity_score = 1.0
    if total_facts > 0:
        fidelity_score = 1.0 - (lost_facts / total_facts)
        
    return {
        "fidelity_score": round(fidelity_score, 4),
        "total_facts": total_facts,
        "lost_facts": lost_facts,
        "drift": {
            "lost_numbers": sorted(list(lost_nums)),
            "lost_identifiers": sorted(list(lost_ids)),
            "lost_constraints": sorted(list(lost_cons))
        },
        "preserved": {
            "numbers": sorted(list(o_nums & r_nums)),
            "identifiers": sorted(list(o_ids & r_ids)),
            "constraints": sorted(list(o_cons & r_cons))
        }
    }

if __name__ == "__main__":
    if len(sys.argv) == 3:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            orig = f.read()
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            rewr = f.read()
        print(json.dumps(transmit_check(orig, rewr), indent=2))
    else:
        print("Usage: python transmit_check.py <original.txt> <rewritten.txt>")
