from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# =========================================================
# CREATE EXCEL REPORT
# =========================================================

def create_excel_report(
    fused_data,
    final_result,
    output_path="FixAI_Fusion_Report.xlsx"
):

    workbook = Workbook()

    worksheet = workbook.active
    worksheet.title = "Data Fusion"

    # =====================================================
    # HEADERS
    # =====================================================

    worksheet.append([
        "Source",
        "Field",
        "Value"
    ])

    # =====================================================
    # HEADER STYLE
    # =====================================================

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78"
    )

    header_font = Font(
        bold=True,
        color="FFFFFF"
    )

    thin_border = Border(
        bottom=Side(
            style="thin",
            color="D9E1F2"
        )
    )

    for cell in worksheet[1]:

        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center"
        )

    # =====================================================
    # HELPER FUNCTION
    # =====================================================

    def add_row(
        source,
        field,
        value
    ):

        if value is None:
            value = ""

        # Convert lists/dictionaries to readable text
        if isinstance(value, list):

            if not value:
                value = ""

            elif all(
                isinstance(item, dict)
                for item in value
            ):

                value = str(value)

            else:

                value = ", ".join(
                    str(item)
                    for item in value
                )

        elif isinstance(value, dict):

            value = str(value)

        worksheet.append([
            source,
            field,
            value
        ])

    # =====================================================
    # 1. GEMINI IMAGE ANALYSIS
    # =====================================================

    image_analysis = fused_data.get(
        "image_analysis",
        {}
    )

    image_fields = [
        "issue",
        "category",
        "severity",
        "confidence",
        "possible_causes",
        "recommended_service"
    ]

    for field in image_fields:

        if field in image_analysis:

            add_row(
                "Gemini Image Analysis",
                field.replace("_", " ").title(),
                image_analysis[field]
            )

    # =====================================================
    # 2. GEOCODING
    # =====================================================

    location = fused_data.get(
        "location",
        {}
    )

    add_row(
        "Geocoding API",
        "Address",
        location.get("address")
    )

    add_row(
        "Geocoding API",
        "Latitude",
        location.get("latitude")
    )

    add_row(
        "Geocoding API",
        "Longitude",
        location.get("longitude")
    )

    # =====================================================
    # 3. WEATHER
    # =====================================================

    weather = fused_data.get(
        "weather",
        {}
    )

    for field, value in weather.items():

        add_row(
            "Weather API",
            field.replace("_", " ").title(),
            value
        )

    # =====================================================
    # 4. AIR QUALITY
    # =====================================================

    air_quality = fused_data.get(
        "air_quality",
        {}
    )

    for field, value in air_quality.items():

        add_row(
            "Air Quality API",
            field.replace("_", " ").upper(),
            value
        )

    # =====================================================
    # 5. DEFECT KNOWLEDGE
    # =====================================================

    defect_knowledge = fused_data.get(
        "defect_knowledge",
        {}
    )

    if defect_knowledge:

        if isinstance(
            defect_knowledge,
            dict
        ):

            for field, value in defect_knowledge.items():

                add_row(
                    "Defect Knowledge Dataset",
                    field.replace(
                        "_",
                        " "
                    ).title(),
                    value
                )

        else:

            add_row(
                "Defect Knowledge Dataset",
                "Knowledge",
                defect_knowledge
            )

    # =====================================================
    # 6. LOCAL PROFESSIONALS
    # =====================================================

    local_services = fused_data.get(
        "local_services",
        []
    )

    for professional in local_services:

        if not isinstance(
            professional,
            dict
        ):
            continue

        # Add every actual field returned
        # by YOUR REST API

        for field, value in professional.items():

            add_row(
                "FixAI Maharashtra REST API",
                field.replace(
                    "_",
                    " "
                ).title(),
                value
            )

        # Separator between professionals
        add_row(
            "FixAI Maharashtra REST API",
            "",
            ""
        )

    # =====================================================
    # 7. FINAL GEMINI REASONING
    # =====================================================

    final_fields = [
        "issue",
        "category",
        "severity",
        "confidence",
        "likely_causes",
        "environmental_factors",
        "recommended_action",
        "recommended_service",
        "professional",
        "explanation",
        "warning"
    ]

    for field in final_fields:

        if field in final_result:

            value = final_result[field]

            # Professional is usually a dictionary
            if (
                field == "professional"
                and isinstance(value, dict)
            ):

                for professional_field, professional_value in value.items():

                    add_row(
                        "Final Gemini Reasoning",
                        f"Professional - {professional_field.replace('_', ' ').title()}",
                        professional_value
                    )

            else:

                add_row(
                    "Final Gemini Reasoning",
                    field.replace(
                        "_",
                        " "
                    ).title(),
                    value
                )

    # =====================================================
    # FORMATTING
    # =====================================================

    for row in worksheet.iter_rows():

        for cell in row:

            cell.border = thin_border

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )

    # =====================================================
    # COLUMN WIDTHS
    # =====================================================

    worksheet.column_dimensions["A"].width = 32
    worksheet.column_dimensions["B"].width = 35
    worksheet.column_dimensions["C"].width = 80

    # =====================================================
    # FREEZE HEADER
    # =====================================================

    worksheet.freeze_panes = "A2"

    # =====================================================
    # SAVE
    # =====================================================

    workbook.save(
        output_path
    )

    return output_path