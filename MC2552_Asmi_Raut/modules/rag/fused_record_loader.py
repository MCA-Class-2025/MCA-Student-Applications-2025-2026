import pandas as pd


FUSED_CSV = "data/api_results/final_fused_dataset_clean.csv"


def is_unavailable(value):
    """
    Returns True for values that should not be included
    as meaningful knowledge in the RAG document.
    """
    if value is None:
        return True

    value = str(value).strip()

    unavailable_values = {
        "",
        "NOT_AVAILABLE",
        "NOT_APPLICABLE",
        "NOT_APPLICABLE_PRIVATE_IP",
        "NO_MATCH",
        "NO_DATA",
    }

    return value in unavailable_values


def format_field_name(column_name):
    """
    Converts database-style column names into readable labels.
    """
    return column_name.replace("_", " ").strip().title()


def row_to_document(row):
    """
    Converts one fused CSV row into one textual RAG document.
    """

    sections = []

    # ---------------------------------------------------------
    # RECORD INFORMATION
    # ---------------------------------------------------------

    record_fields = [
        "working_record_id",
        "attack",
        "cic_label",
        "ip_traffic_class",
        "enrichment_ip",
        "threat_ip",
        "ip_entity_role",
        "cic_flow_id",
        "cic_timestamp",
    ]

    record_lines = []

    for column in record_fields:

        if column in row.index:

            value = row[column]

            if not is_unavailable(value):

                record_lines.append(
                    f"{format_field_name(column)}: {value}"
                )

    if record_lines:

        sections.append(
            "RECORD INFORMATION\n" +
            "\n".join(record_lines)
        )

    # ---------------------------------------------------------
    # NETWORK INFORMATION
    # ---------------------------------------------------------

    network_fields = [
        "duration",
        "protocol_type",
        "service",
        "flag",
        "src_bytes",
        "dst_bytes",
        "land",
        "wrong_fragment",
        "urgent",
        "hot",
        "num_failed_logins",
        "logged_in",
        "num_compromised",
        "root_shell",
        "su_attempted",
        "num_root",
        "num_file_creations",
        "num_shells",
        "num_access_files",
        "num_outbound_cmds",
        "is_host_login",
        "is_guest_login",
        "count",
        "srv_count",
        "serror_rate",
        "srv_serror_rate",
        "rerror_rate",
        "srv_rerror_rate",
        "same_srv_rate",
        "diff_srv_rate",
        "srv_diff_host_rate",
        "dst_host_count",
        "dst_host_srv_count",
        "dst_host_same_srv_rate",
        "dst_host_diff_srv_rate",
        "dst_host_same_src_port_rate",
        "dst_host_srv_diff_host_rate",
        "dst_host_serror_rate",
        "dst_host_srv_serror_rate",
        "dst_host_rerror_rate",
        "dst_host_srv_rerror_rate",
        "difficulty_level",
        "cic_source_ip",
        "cic_source_port",
        "cic_destination_ip",
        "cic_destination_port",
        "cic_protocol",
    ]

    network_lines = []

    for column in network_fields:

        if column in row.index:

            value = row[column]

            if not is_unavailable(value):

                network_lines.append(
                    f"{format_field_name(column)}: {value}"
                )

    if network_lines:

        sections.append(
            "NETWORK INFORMATION\n" +
            "\n".join(network_lines)
        )

    # ---------------------------------------------------------
    # API / EXTERNAL INTELLIGENCE
    # ---------------------------------------------------------

    api_prefixes = [
        "abuseipdb_",
        "virustotal_",
        "otx_",
        "shodan_",
        "threatfox_",
    ]

    api_lines = []

    for column in row.index:

        column_lower = column.lower()

        # Only API-related columns
        if not any(
            column_lower.startswith(prefix)
            for prefix in api_prefixes
        ):
            continue

        # Do not put raw error-details into normal knowledge text
        if "error_detail" in column_lower:
            continue

        value = row[column]

        if is_unavailable(value):
            continue

        api_lines.append(
            f"{format_field_name(column)}: {value}"
        )

    if api_lines:

        sections.append(
            "EXTERNAL API INTELLIGENCE\n" +
            "\n".join(api_lines)
        )

    # ---------------------------------------------------------
    # FINAL DOCUMENT
    # ---------------------------------------------------------

    return "\n\n".join(sections)


def build_documents(csv_path=FUSED_CSV):

    df = pd.read_csv(
        csv_path,
        dtype=str,
        keep_default_na=False
    )

    df.columns = df.columns.str.strip()

    documents = []

    for _, row in df.iterrows():

        document = row_to_document(row)

        if document.strip():

            documents.append(document)

    return documents


if __name__ == "__main__":

    documents = build_documents()

    print("=" * 70)
    print("SECURESENSE AI - FUSED RECORD CONVERSION")
    print("=" * 70)

    print("CSV records:", len(documents))

    if documents:

        print("\nFIRST DOCUMENT")
        print("=" * 70)
        print(documents[0])