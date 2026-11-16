import json
from pathlib import Path


class MITREAttack:

    def __init__(self):

        # -----------------------------------------
        # Locate enterprise-attack.json
        # -----------------------------------------

        project_root = Path(__file__).resolve().parent.parent

        self.data_file = (
            project_root
            / "data"
            / "enterprise-attack.json"
        )

        if not self.data_file.exists():

            raise FileNotFoundError(
                f"MITRE ATT&CK dataset not found: {self.data_file}"
            )

        # -----------------------------------------
        # Load JSON
        # -----------------------------------------

        print("Loading MITRE ATT&CK dataset...")

        with open(
            self.data_file,
            "r",
            encoding="utf-8"
        ) as file:

            self.data = json.load(file)

        self.objects = self.data.get(
            "objects",
            []
        )

        print(
            f"MITRE dataset loaded: "
            f"{len(self.objects)} objects"
        )


    # =========================================
    # Get ATT&CK Techniques
    # =========================================

    def get_techniques(self):

        techniques = []

        for obj in self.objects:

            if obj.get("type") != "attack-pattern":
                continue

            # Ignore revoked/deprecated techniques
            if obj.get("revoked", False):
                continue

            if obj.get("x_mitre_deprecated", False):
                continue

            techniques.append({

                "id": obj.get(
                    "external_references",
                    [{}]
                )[0].get("external_id"),

                "name": obj.get("name"),

                "description": obj.get(
                    "description",
                    ""
                ),

                "created": obj.get(
                    "created"
                ),

                "modified": obj.get(
                    "modified"
                )

            })

        return techniques


    # =========================================
    # Search ATT&CK Techniques
    # =========================================

    def search_technique(self, keyword):

        keyword = keyword.lower()

        results = []

        for obj in self.objects:

            if obj.get("type") != "attack-pattern":
                continue

            if obj.get("revoked", False):
                continue

            if obj.get("x_mitre_deprecated", False):
                continue

            name = obj.get(
                "name",
                ""
            )

            description = obj.get(
                "description",
                ""
            )

            if (
                keyword in name.lower()
                or keyword in description.lower()
            ):

                technique_id = None

                for reference in obj.get(
                    "external_references",
                    []
                ):

                    if (
                        reference.get(
                            "source_name"
                        ) == "mitre-attack"
                        and reference.get(
                            "external_id"
                        )
                    ):

                        technique_id = reference.get(
                            "external_id"
                        )

                        break

                results.append({

                    "id": technique_id,

                    "name": name,

                    "description": description

                })

        return results


    # =========================================
    # Get Technique By ID
    # =========================================

    def get_technique_by_id(self, technique_id):

        technique_id = technique_id.upper()

        for obj in self.objects:

            if obj.get("type") != "attack-pattern":
                continue

            if obj.get("revoked", False):
                continue

            if obj.get("x_mitre_deprecated", False):
                continue

            for reference in obj.get(
                "external_references",
                []
            ):

                if (
                    reference.get(
                        "source_name"
                    ) == "mitre-attack"
                    and reference.get(
                        "external_id"
                    ) == technique_id
                ):

                    return {

                        "id": technique_id,

                        "name": obj.get(
                            "name"
                        ),

                        "description": obj.get(
                            "description",
                            ""
                        )

                    }

        return None


# =============================================
# Terminal Test
# =============================================

if __name__ == "__main__":

    print("=" * 60)
    print("MITRE ATT&CK STATIC DATASET TEST")
    print("=" * 60)

    mitre = MITREAttack()

    # -----------------------------------------
    # Count techniques
    # -----------------------------------------

    techniques = mitre.get_techniques()

    print("\nTotal Techniques:")
    print(len(techniques))

    # -----------------------------------------
    # Test search
    # -----------------------------------------

    print("\nTechnique Search")
    print("-" * 40)

    results = mitre.search_technique(
        "command and scripting"
    )

    for technique in results[:5]:

        print(
            "\nTechnique ID:",
            technique["id"]
        )

        print(
            "Name:",
            technique["name"]
        )

        description = technique["description"]

        if len(description) > 300:
            description = description[:300] + "..."

        print(
            "Description:",
            description
        )

    # -----------------------------------------
    # Test specific technique
    # -----------------------------------------

    print("\nSpecific Technique Test")
    print("-" * 40)

    technique = mitre.get_technique_by_id(
        "T1059"
    )

    if technique:

        print(
            "Technique ID:",
            technique["id"]
        )

        print(
            "Name:",
            technique["name"]
        )

        print(
            "Description:",
            technique["description"][:300],
            "..."
        )

    else:

        print(
            "T1059 not found."
        )