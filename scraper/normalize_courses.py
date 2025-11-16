import json
import re

INPUT_FILE = "rpi_courses.json"
OUTPUT_FILE = "normalized_courses.json"


# ---------------------------------------------------
# Convert raw credits into an integer
# If range → choose the highest value
# ---------------------------------------------------
def parse_credits(raw):
    """
    Convert credits string into an integer.
    Examples:
    '4'       -> 4
    '1 to 4'  -> 4
    '1-4'     -> 4
    '0 or 4'  -> 4
    'Variable' -> 0 (no numbers)
    """
    if not raw or raw.strip() == "":
        return 0

    raw = raw.strip()
    raw_lower = raw.lower()

    # Normal integer
    if raw.isdigit():
        return int(raw)

    # Extract ALL numbers in the string
    nums = re.findall(r"\d+", raw_lower)
    if nums:
        return int(max(nums))  # return highest value

    # If no numeric info at all
    return 0


# ---------------------------------------------------
# Convert offered-term text into a list like:
# ["Fall", "Spring"]
# ---------------------------------------------------
def parse_semesters(offered_raw):
    if not offered_raw or offered_raw.strip() == "":
        return ["Fall", "Spring"]  # default safe assumption

    text = offered_raw.lower()

    semesters = []

    # YEARLY → both fall + spring
    if "yearly" in text:
        semesters = ["Fall", "Spring"]
    else:
        if "fall" in text:
            semesters.append("Fall")
        if "spring" in text:
            semesters.append("Spring")
        if "summer" in text:
            semesters.append("Summer")

    # If we still have no semesters after analysis
    if not semesters:
        # “annually” or “term annually” etc → do NOT force anything extra
        # Just assume all terms (safe fallback)
        semesters = ["Fall", "Spring"]

    return semesters


# ---------------------------------------------------
# Convert prerequisites text into an array
# ---------------------------------------------------
def parse_list(raw):
    if not raw or "none" in raw.lower():
        return []
    return [item.strip() for item in raw.split(",")]


# ---------------------------------------------------
# Main normalizer
# ---------------------------------------------------
def convert():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    normalized = []

    for c in data:
        normalized.append({
            "course_id": c.get("Code"),
            "name": c.get("Name"),
            "credits": parse_credits(c.get("Credits")),
            "semesters_offered": parse_semesters(c.get("Offered")),
            "prerequisites": parse_list(c.get("Prerequisites"))
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=4)

    print(f"✨ Wrote {OUTPUT_FILE} successfully! ({len(normalized)} courses)")


# ---------------------------------------------------
# Run the converter
# ---------------------------------------------------
if __name__ == "__main__":
    convert()
