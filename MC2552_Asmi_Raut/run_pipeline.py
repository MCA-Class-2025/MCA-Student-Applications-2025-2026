"""Run the authoritative enrichment_ip API regeneration and fusion workflow."""

from modules.api.regenerate_enrichment_apis import main as regenerate_apis
from modules.api.final_api_fusion import main as run_fusion


def main():
    regenerate_apis()
    run_fusion()


if __name__ == "__main__":
    main()
