# Basket of item IDs to track (ore, herbs, cloth - Midnight expansion).
#
# IDs confirmed via find_item_ids.py against Blizzard's own item search API.
# 4 names (Mana Lily, Umbral Tin Ore, Pure Loanite, Sunfire Silk) didn't
# resolve to an exact match and need manual lookup on Wowhead - the
# community-guide names were likely slightly off from the real item name.
# Add them here once confirmed, following the same "id,  # Name" format.

ITEM_BASKET = [
    236780,   # Nocturnal Lotus (single-tier)
    237366,   # Dazzling Thorium (single-tier)
    236775,   # Azeroot (Gold)
    236771,   # Sanguithorn (Gold)
    236777,   # Argentleaf (Gold)
    237361,   # Refulgent Copper Ore (Gold)
    236965,   # Bright Linen (Gold)
    237017,   # Arcanoweave (Gold)
    238203,   # Gloaming Alloy (Gold)
    238205,   # Sterling Alloy (Gold)
    236779,   # Mana Lily (Gold)
    244633,   # Infused Scalewoven Hide (Gold)
    244635,   # Sin'dorei Armor Banding (Gold)
    238521,   # Void-Tempered Plating (Gold)
]