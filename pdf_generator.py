from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def create_pdf(content, image_path=None):

    filename = "Interior_Design_Report.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "AI Interior Designer Report",
            styles["Title"]
        )
    )

    story.append(Spacer(1, 20))

    content = content.replace("\n", "<br/>")

    story.append(
        Paragraph(
            content,
            styles["BodyText"]
        )
    )

    doc.build(story)

    return filename