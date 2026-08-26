"""Find call sites of defaulted-key APIs that pass no key. Read-only."""
import io, os, re

FNS = ["prepare_roster","prepare_selection_move","prepare_subclass_equip",
       "prepare_item_republish","prepare_subclass_selection","prepare_ability_change",
       "prepare_initial","prepare_banner","prepare_banner_refresh",
       "prepare_roster_appearance_refresh","load_account","load_entitlements",
       "write_back","persist_subclass_equip","persist_ability_change",
       "sign_on","bap","set_primary_soid","set_selected_character",
       "account_snapshot","investment_snapshot","apply_ability_change",
       "commit_subclass_selection","equip_subclass_item",
       "subclass_equip_request_valid","publish_family5"]

def balanced(text, start):
    depth, i = 0, start
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return text[start:start + 200]

hits = []
for root, _, files in os.walk("Sunrise/src"):
    for name in files:
        if not name.endswith(".cpp"):
            continue
        path = os.path.join(root, name)
        if "_test.cpp" in name:
            continue
        text = io.open(path, encoding="utf-8", errors="replace").read()
        for fn in FNS:
            for m in re.finditer(r'\b' + fn + r'\s*\(', text):
                args = balanced(text, m.end() - 1)
                if re.search(r'\baccountKey\b|\bkey\b|\bkLegacyAccount\b|AccountKey', args):
                    continue
                line = text[:m.start()].count("\n") + 1
                hits.append((path.replace("Sunrise/src/", ""), line, fn,
                             " ".join(args.split())[:70]))
for h in sorted(hits):
    print("%-58s %-5d %-28s %s" % h)
print("\nTOTAL UNKEYED CALL SITES:", len(hits))
