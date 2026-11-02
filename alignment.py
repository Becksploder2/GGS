"""Heuristic tile adjacency layout for *uncompressed* 8x8 Genesis 4bpp tiles.

No game metadata is inferred. This is a reversible visual reordering only:
map[position] = original tile index. It cannot decode compression/tilemaps.
"""
def edge_cost(a, b, direction):
    """Return edge mismatch count (lower is better) for touching tiles."""
    if direction == 'right':
        return sum(a[y*8+7] != b[y*8] for y in range(8))
    if direction == 'down':
        return sum(a[56+x] != b[x] for x in range(8))
    raise ValueError('Unknown direction')

def layout_cost(tiles, order, columns):
    cost = 0
    for pos, idx in enumerate(order):
        x = pos % columns
        y = pos // columns
        if x:
            cost += edge_cost(tiles[order[pos-1]], tiles[idx], 'right')
        if y:
            cost += edge_cost(tiles[order[pos-columns]], tiles[idx], 'down')
    return cost

def auto_align(tiles, columns):
    """Greedy edge matcher with deterministic tie breaking and safe fallback.

    Chooses a reversible ordering. Only accepts it if total adjacent pixel
    mismatch is lower than original tile order. This is not sprite detection.
    """
    count = len(tiles)
    if count == 0 or columns < 1:
        return list(range(count)), 0, 0
    if any(len(tile) != 64 for tile in tiles):
        raise ValueError('Expected 64 palette-index pixels per tile.')
    original = list(range(count))
    baseline = layout_cost(tiles, original, columns)
    if count < 3:
        return original, baseline, baseline
    remaining = set(range(count))
    # The first tile is an anchor. A ROM tilemap, screenshot, or manual
    # anchor is required for stronger layout inference.
    order = [0]
    remaining.remove(0)
    while remaining:
        pos = len(order)
        left = order[pos-1] if pos % columns else None
        above = order[pos-columns] if pos >= columns else None
        def candidate_cost(idx):
            mismatch = 0
            if left is not None:
                mismatch += edge_cost(tiles[left], tiles[idx], 'right')
            if above is not None:
                mismatch += edge_cost(tiles[above], tiles[idx], 'down')
            # Preserve local source ordering on equal edge scores
            return (mismatch, abs(idx-pos), idx)
        nxt = min(remaining,key=candidate_cost)
        order.append(nxt)
        remaining.remove(nxt)
    score = layout_cost(tiles,order,columns)
    if score >= baseline:
        return original, baseline, baseline
    return order, baseline, score
