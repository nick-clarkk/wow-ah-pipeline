# Basket of item IDs to track (ore, herbs, cloth - Midnight expansion).
#
# IDs confirmed via find_item_ids.py against Blizzard's own item search API.
# 4 names (Mana Lily, Umbral Tin Ore, Pure Loanite, Sunfire Silk) didn't
# resolve to an exact match and need manual lookup on Wowhead - the
# community-guide names were likely slightly off from the real item name.
# Add them here once confirmed, following the same "id,  # Name" format.

ITEM_BASKET = [
    236780,   # Nocturnal Lotus (herb)
    236775,   # Azeroot (herb)
    236771,   # Sanguithorn (herb)
    236777,   # Argentleaf (herb)
    237361,   # Refulgent Copper Ore (ore)
    237366,   # Dazzling Thorium (ore)
    236965,   # Bright Linen (cloth)
    237018,   # Arcanoweave (cloth)
]
