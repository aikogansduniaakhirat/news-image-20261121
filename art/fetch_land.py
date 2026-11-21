"""Build a compact land-ring cache from the local public-domain Natural Earth data."""

import json
import math


SOURCE = "/home/ubuntu/makefun/work/land/ne_110m_land.geojson"
OUTPUT = "/home/ubuntu/makefun/work/repos/news-image-20261121/art/land_cache.json"
TOLERANCE = 0.55


def simplify(points, tolerance):
    """Douglas-Peucker using point-to-segment distance and an explicit stack."""
    if len(points) <= 2:
        return points[:]
    keep = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        ax, ay = points[start]
        bx, by = points[end]
        dx, dy = bx - ax, by - ay
        length_squared = dx * dx + dy * dy
        farthest = -1
        max_distance = tolerance
        for index in range(start + 1, end):
            px, py = points[index]
            if length_squared:
                fraction = ((px - ax) * dx + (py - ay) * dy) / length_squared
                fraction = max(0.0, min(1.0, fraction))
                distance = math.hypot(px - ax - fraction * dx,
                                      py - ay - fraction * dy)
            else:
                distance = math.hypot(px - ax, py - ay)
            if distance > max_distance:
                farthest = index
                max_distance = distance
        if farthest != -1:
            keep.add(farthest)
            stack.append((start, farthest))
            stack.append((farthest, end))
    return [points[index] for index in sorted(keep)]


def main():
    with open(SOURCE, encoding="utf-8") as source:
        collection = json.load(source)
    rings = []
    for feature in collection["features"]:
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        if geometry["type"] == "Polygon":
            polygons = [geometry["coordinates"]]
        elif geometry["type"] == "MultiPolygon":
            polygons = geometry["coordinates"]
        else:
            raise ValueError("Expected Polygon or MultiPolygon geometry")
        for polygon in polygons:
            for ring in polygon:
                # Deliberately drop out-of-range vertices, without interpolation.
                points = [(point[0], point[1]) for point in ring
                          if -58.0 <= point[1] <= 83.0]
                if len(set(points)) < 3:
                    continue
                width = max(p[0] for p in points) - min(p[0] for p in points)
                height = max(p[1] for p in points) - min(p[1] for p in points)
                if width < 1.2 and height < 1.2:
                    continue
                if points[0] != points[-1]:
                    points.append(points[0])
                reduced = simplify(points, TOLERANCE)
                rounded = [[round(lon, 1), round(lat, 1)] for lon, lat in reduced]
                if len({tuple(point) for point in rounded}) < 3:
                    continue
                rings.append(rounded)
    payload = json.dumps({"rings": rings}, separators=(",", ":"), allow_nan=False)
    encoded = payload.encode("utf-8")
    with open(OUTPUT, "wb") as output:
        output.write(encoded)
    total_points = sum(len(ring) for ring in rings)
    print(f"Rings kept: {len(rings)}; total points: {total_points}; "
          f"output bytes: {len(encoded)}")


if __name__ == "__main__":
    main()
