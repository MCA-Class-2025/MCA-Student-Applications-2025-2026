import pandas as pd


# =========================================================
# LOAD DEFECT KNOWLEDGE
# =========================================================

DEFECT_FILE = "data/building_defect_knowledge.csv"

defect_df = pd.read_csv(DEFECT_FILE)


# =========================================================
# NORMALIZE DEFECT
# =========================================================

def normalize_defect(defect):

    if not defect:
        return ""

    defect = str(defect).lower().strip()


    # Plaster / render problems
    if any(word in defect for word in [
        "peeling",
        "plaster",
        "render",
        "delaminat",
        "detach"
    ]):
        return "detachment"


    # Water problems
    if any(word in defect for word in [
        "leak",
        "leakage",
        "seepage",
        "water"
    ]):
        return "water"


    # Moisture problems
    if any(word in defect for word in [
        "moisture",
        "damp",
        "dampness"
    ]):
        return "moisture"


    # Cracks
    if any(word in defect for word in [
        "crack",
        "cracking",
        "fracture"
    ]):
        return "crack"


    # Rust
    if any(word in defect for word in [
        "rust",
        "corrosion"
    ]):
        return "corrosion"


    return defect


# =========================================================
# SEARCH DEFECT KNOWLEDGE
# =========================================================

def search_defects(
    defect=None,
    element=None,
    location=None
):

    if defect is None:
        return []


    normalized = normalize_defect(
        defect
    )


    result = defect_df.copy()


    # =====================================================
    # SEARCH ACROSS ENTIRE DATASET
    # =====================================================

    matches = []

    for _, row in result.iterrows():

        row_text = " ".join(
            str(value).lower()
            for value in row.values
        )


        # -----------------------------------------------
        # NORMALIZED MATCHES
        # -----------------------------------------------

        if normalized == "detachment":

            if any(word in row_text for word in [
                "detach",
                "peel",
                "plaster",
                "render"
            ]):

                matches.append(row)


        elif normalized == "water":

            if any(word in row_text for word in [
                "water",
                "leak",
                "seepage"
            ]):

                matches.append(row)


        elif normalized == "moisture":

            if any(word in row_text for word in [
                "moisture",
                "damp"
            ]):

                matches.append(row)


        elif normalized == "crack":

            if any(word in row_text for word in [
                "crack",
                "fracture"
            ]):

                matches.append(row)


        elif normalized == "corrosion":

            if any(word in row_text for word in [
                "corrosion",
                "rust"
            ]):

                matches.append(row)


        else:

            if normalized in row_text:

                matches.append(row)


    # =====================================================
    # CONVERT TO DICTIONARY
    # =====================================================

    if not matches:

        return []


    result_df = pd.DataFrame(
        matches
    )


    return result_df.to_dict(
        orient="records"
    )