from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

pdf_path = "prelabel_tool_update.pdf"

doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    rightMargin=0.75 * inch,
    leftMargin=0.75 * inch,
    topMargin=0.75 * inch,
    bottomMargin=0.75 * inch,
)

styles = getSampleStyleSheet()
story = []

title = "Pre-label Tool Update"
body = """
Hi, quick update on the pre-label tool work.<br/><br/>

I built a web-based multi-view pre-label tool prototype, with the CSS-backed version structured so everything can run online. The UI supports:<br/><br/>

- listing sequences that need pre-labeling<br/>
- opening a selected sequence<br/>
- viewing 4 camera MP4s: front, back, left, and right<br/>
- drawing one bounding box per camera view<br/>
- required metadata fields: calib_sequence, object_id, person_id, action_description, and action_language<br/>
- disabling Submit until all required fields are filled and all 4 bounding boxes are drawn<br/>
- generating hoi_metadata.yaml<br/>
- uploading hoi_metadata.yaml back to CSS<br/>
- returning to the sequence list after submit<br/><br/>

The intended CSS-backed flow is:<br/><br/>

CSS MP4s -> browser streams videos -> user draws boxes -> tool uploads hoi_metadata.yaml back to CSS<br/><br/>

So the user should not need to store or download videos locally. The tool will stream the MP4s from CSS and write the metadata file back to CSS.<br/><br/>

For safety, development is configured to use the test prefix first:<br/><br/>

v2d/multiview_test/sc_office_4exo_1/data/&lt;sequence_name&gt;/<br/><br/>

Before switching to real CSS data, we should provide/confirm the CSS S3-compatible configuration:<br/><br/>

- endpoint URL<br/>
- bucket/container name<br/>
- access key / secret key source<br/>
- signature version, e.g. s3 or s3v4<br/>
- whether path-style addressing is required<br/>
- region name if required<br/><br/>

Once those are provided, the tool can list sequences from CSS, stream the 4 MP4s online, and upload hoi_metadata.yaml back to the test CSS folder.
"""

story.append(Paragraph(title, styles["Title"]))
story.append(Spacer(1, 0.2 * inch))
story.append(Paragraph(body, styles["BodyText"]))

doc.build(story)

print(f"Created {pdf_path}")
