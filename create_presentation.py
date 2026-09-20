"""
create_presentation.py
======================
Builds a beautiful 5-slide Google Slides portfolio for Ali Naeimabadi.

Slide themes  — dark navy background, teal/cyan accents, coloured cards.

Slide layout:
  1. Title — name, role, tagline, decorative circles
  2. Professional Summary — 3 metric KPI cards + summary text
  3. Technical Skills — 6 skill-category cards in 2×3 grid
  4. Career Highlights — 4 achievement cards with coloured left-bars
  5. Education & Publications — 2 education + 3 publication cards
"""

import sys, uuid
sys.path.insert(0, '.')

from connector import GoogleDriveConnector
from googleapiclient.discovery import build

# ── Auth & services ───────────────────────────────────────────────────────────
conn       = GoogleDriveConnector()
slides_svc = build('slides', 'v1', credentials=conn._creds)

DEMO_FOLDER_ID = "1PC6FzJrGecGZGvOCcozFXF59kF7Lib9t"   # created in demo

# ── EMU helpers ───────────────────────────────────────────────────────────────
W = 9144000   # slide width  (10 in)
H = 6858000   # slide height (7.5 in)

def pw(p):  return int(W * p / 100)
def ph(p):  return int(H * p / 100)
def nid():  return 'o' + uuid.uuid4().hex[:14]   # unique object id

# ── Colour palette ────────────────────────────────────────────────────────────
def rgb(r, g, b): return {"red": r/255, "green": g/255, "blue": b/255}

NAVY    = rgb( 13,  27,  42)   # dark background
NAVY2   = rgb( 22,  44,  68)   # card / header background
TEAL    = rgb( 32, 178, 170)   # primary accent
LTBLUE  = rgb( 79, 195, 247)   # secondary accent
GREEN   = rgb(102, 187, 106)
AMBER   = rgb(255, 183,  77)
PINK    = rgb(240,  98, 146)
PURPLE  = rgb(186, 104, 200)
WHITE   = rgb(255, 255, 255)
LGRAY   = rgb(176, 190, 197)
MGRAY   = rgb(100, 121, 135)

# ── Low-level request builders ────────────────────────────────────────────────

def _elem_props(slide_id, x, y, w, h):
    return {
        "pageObjectId": slide_id,
        "size": {
            "width":  {"magnitude": pw(w), "unit": "EMU"},
            "height": {"magnitude": ph(h), "unit": "EMU"},
        },
        "transform": {
            "scaleX": 1, "scaleY": 1, "shearX": 0, "shearY": 0,
            "translateX": pw(x), "translateY": ph(y), "unit": "EMU",
        },
    }

def shape(oid, slide_id, x, y, w, h, kind="RECTANGLE"):
    return {"createShape": {"objectId": oid, "shapeType": kind,
                            "elementProperties": _elem_props(slide_id, x, y, w, h)}}

def textbox(oid, slide_id, x, y, w, h):
    return shape(oid, slide_id, x, y, w, h, "TEXT_BOX")

def solid_fill(oid, color, alpha=1.0):
    return {"updateShapeProperties": {
        "objectId": oid,
        "shapeProperties": {
            "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": color}, "alpha": alpha}},
            "outline": {"propertyState": "NOT_RENDERED"},
        },
        "fields": "shapeBackgroundFill,outline",
    }}

def transparent(oid):
    return {"updateShapeProperties": {
        "objectId": oid,
        "shapeProperties": {
            "shapeBackgroundFill": {"propertyState": "NOT_RENDERED"},
            "outline": {"propertyState": "NOT_RENDERED"},
        },
        "fields": "shapeBackgroundFill,outline",
    }}

def text(oid, content):
    return {"insertText": {"objectId": oid, "text": content}}

def style(oid, color, size, bold=False, italic=False, font="Arial"):
    return {"updateTextStyle": {
        "objectId": oid,
        "textRange": {"type": "ALL"},
        "style": {
            "foregroundColor": {"opaqueColor": {"rgbColor": color}},
            "fontSize": {"magnitude": size, "unit": "PT"},
            "bold": bold, "italic": italic,
            "fontFamily": font,
        },
        "fields": "foregroundColor,fontSize,bold,italic,fontFamily",
    }}

def align(oid, a="CENTER"):
    # Slides API uses START/CENTER/END (not LEFT/RIGHT)
    _map = {"LEFT": "START", "RIGHT": "END", "CENTER": "CENTER"}
    return {"updateParagraphStyle": {
        "objectId": oid,
        "textRange": {"type": "ALL"},
        "style": {"alignment": _map.get(a, a)},
        "fields": "alignment",
    }}

def slide_bg(slide_id, color):
    return {"updatePageProperties": {
        "objectId": slide_id,
        "pageProperties": {"pageBackgroundFill": {"solidFill": {"color": {"rgbColor": color}}}},
        "fields": "pageBackgroundFill",
    }}

# ── Composite helpers ─────────────────────────────────────────────────────────

def card(reqs, slide_id, x, y, w, h, fill=NAVY2, radius="ROUND_RECTANGLE"):
    cid = nid()
    reqs += [shape(cid, slide_id, x, y, w, h, radius), solid_fill(cid, fill)]
    return cid

def accent_bar(reqs, slide_id, x, y, w, h, color):
    bid = nid()
    reqs += [shape(bid, slide_id, x, y, w, h), solid_fill(bid, color)]

def label(reqs, slide_id, x, y, w, h, txt, color, size, bold=False, italic=False, alignment="LEFT"):
    lid = nid()
    reqs += [textbox(lid, slide_id, x, y, w, h), transparent(lid),
             text(lid, txt), style(lid, color, size, bold=bold, italic=italic), align(lid, alignment)]

def header_band(reqs, slide_id, title_text, accent_color=TEAL):
    """Consistent dark header band used on slides 2-5."""
    hbg = nid()
    reqs += [shape(hbg, slide_id, 0, 0, 100, 17), solid_fill(hbg, NAVY2)]
    hline = nid()
    reqs += [shape(hline, slide_id, 0, 16.5, 100, 0.7), solid_fill(hline, accent_color)]
    lbar = nid()
    reqs += [shape(lbar, slide_id, 0, 0, 1.3, 100), solid_fill(lbar, accent_color)]
    label(reqs, slide_id, 3, 3.5, 80, 12, title_text, WHITE, 30, bold=True)

# ═════════════════════════════════════════════════════════════════════════════
#  Create presentation + move to Demo Folder
# ═════════════════════════════════════════════════════════════════════════════
print("Creating presentation …")
pres   = slides_svc.presentations().create(
    body={"title": "Ali Naeimabadi – AI Engineer Portfolio"}
).execute()
pres_id = pres['presentationId']
print(f"  id = {pres_id}")

# Move into Demo Folder
conn._drive.files().update(
    fileId=pres_id, addParents=DEMO_FOLDER_ID,
    removeParents='root', fields='id,parents'
).execute()
print("  Moved to Demo Folder")

# Get auto-created slide 1
pdata   = slides_svc.presentations().get(presentationId=pres_id).execute()
s1_id   = pdata['slides'][0]['objectId']

# Allocate ids for slides 2-5
s2_id, s3_id, s4_id, s5_id = [nid() for _ in range(4)]

reqs = []

# ─── Delete default elements on slide 1 ──────────────────────────────────────
for elem in pdata['slides'][0].get('pageElements', []):
    reqs.append({"deleteObject": {"objectId": elem['objectId']}})

# ─── Create slides 2-5 ───────────────────────────────────────────────────────
for sid in [s2_id, s3_id, s4_id, s5_id]:
    reqs.append({"createSlide": {"objectId": sid, "slideLayoutReference": {"predefinedLayout": "BLANK"}}})

# ═════════════════════════════════════════════════════════════════════════════
#  SLIDE 1 — TITLE
# ═════════════════════════════════════════════════════════════════════════════
reqs.append(slide_bg(s1_id, NAVY))

# Left accent bar
accent_bar(reqs, s1_id, 0, 0, 2.2, 100, TEAL)

# Decorative circles (right side)
c1 = nid(); reqs += [shape(c1, s1_id, 60, -18, 55, 68, "ELLIPSE"), solid_fill(c1, LTBLUE, 0.07)]
c2 = nid(); reqs += [shape(c2, s1_id, 68, 38,  40, 55, "ELLIPSE"), solid_fill(c2, TEAL,   0.09)]
c3 = nid(); reqs += [shape(c3, s1_id, 82,  4,  15, 20, "ELLIPSE"), solid_fill(c3, AMBER,  0.55)]
c4 = nid(); reqs += [shape(c4, s1_id, 74, 60,  10, 14, "ELLIPSE"), solid_fill(c4, GREEN,  0.70)]

# Horizontal teal rule
r1 = nid(); reqs += [shape(r1, s1_id, 5, 27.5, 55, 0.5), solid_fill(r1, TEAL)]

# Name
label(reqs, s1_id, 5, 30, 60, 18, "Ali Naeimabadi",        WHITE,  52, bold=True)
# Role
label(reqs, s1_id, 5, 50,  60, 10, "ML Engineer  |  AI Engineer",  LTBLUE, 26)
# Tagline
label(reqs, s1_id, 5, 62, 62,  8,
      "6+ Years · Production AI/GenAI · LLMs · Agentic Systems",   LGRAY, 16)
# Contact
label(reqs, s1_id, 5, 80, 65,  6,
      "Calgary, AB  ·  ali.naeim.gdrive@gmail.com  ·  GitHub  ·  LinkedIn",
      MGRAY, 13)

# Bottom footer strip
f1 = nid(); reqs += [shape(f1, s1_id, 0, 93, 100, 7), solid_fill(f1, NAVY2)]
label(reqs, s1_id, 3, 94, 94, 5,
      "WCB-Alberta  ·  Scotiabank  ·  AltaML  ·  Amii  ·  University of Alberta",
      MGRAY, 12, alignment="CENTER")

# ═════════════════════════════════════════════════════════════════════════════
#  SLIDE 2 — PROFESSIONAL SUMMARY
# ═════════════════════════════════════════════════════════════════════════════
reqs.append(slide_bg(s2_id, NAVY))
header_band(reqs, s2_id, "Professional Summary")

# 3 KPI cards
kpis = [
    ("6+",    "Years\nExperience",     LTBLUE),
    ("2,000+","Users\nServed",         GREEN),
    ("65%",   "Faster\nReviews",       AMBER),
]
for i, (val, lbl, col) in enumerate(kpis):
    cx = 5 + i * 31.5
    # card
    k = nid(); reqs += [shape(k, s2_id, cx, 20, 29, 30, "ROUND_RECTANGLE"), solid_fill(k, NAVY2)]
    # coloured top strip
    st = nid(); reqs += [shape(st, s2_id, cx, 20, 29, 3.5), solid_fill(st, col)]
    # big number
    label(reqs, s2_id, cx, 24, 29, 14, val,  col,  36, bold=True, alignment="CENTER")
    # sub-label
    label(reqs, s2_id, cx, 38, 29, 10, lbl, LGRAY, 13,            alignment="CENTER")

# Summary text block
sb = nid(); reqs += [shape(sb, s2_id, 3, 53, 94, 40), solid_fill(sb, NAVY2)]
label(reqs, s2_id, 5, 55, 90, 36,
    "ML Engineer / AI Engineer with 6+ years building production-grade AI systems.\n\n"
    "  \u2192  Agentic RAG systems, LLM apps & AI agents deployed at enterprise scale\n"
    "  \u2192  Expert: LangChain · LangGraph · OpenAI Agents SDK · MCP · Databricks · AWS\n"
    "  \u2192  Published researcher: CIKM 2023 · WSDM 2024 · NCME 2022\n"
    "  \u2192  MSc Computing Science, University of Alberta (GPA 3.84)",
    LGRAY, 14)

# ═════════════════════════════════════════════════════════════════════════════
#  SLIDE 3 — TECHNICAL SKILLS
# ═════════════════════════════════════════════════════════════════════════════
reqs.append(slide_bg(s3_id, NAVY))
header_band(reqs, s3_id, "Technical Skills")

skills = [
    ("NLP / LLM",
     "LangChain · LangGraph · MCP\nOpenAI Agents SDK · Agentic RAG\nLoRA · Q-LoRA · PEFT · Fine-tuning\nLLaMA 4 · Qwen · RoBERTa · VLMs",
     LTBLUE),
    ("DevOps / MLOps",
     "CI/CD · MLOps · LLMOps\nAzure DevOps · GitHub Actions\nKubernetes · Docker\nMLFlow · LangSmith · DeepEval",
     GREEN),
    ("Cloud",
     "Azure · Databricks · GCP\nAWS · Amazon Bedrock\nAmazon SageMaker · Terraform\nData Lake · Microservices",
     AMBER),
    ("Deep Learning",
     "PyTorch · Transformers\nHugging Face · TensorFlow\nCNNs · LSTMs · Attention\nNeural Networks",
     PINK),
    ("Databases",
     "PostgreSQL · MySQL · MongoDB\nFAISS · ChromaDB · Qdrant\nWeaviate · Mosaic AI\nNeo4j (Graph DB)",
     PURPLE),
    ("Languages & Tools",
     "Python (Fluent)\nSQL (Fluent) · C++\nPySpark · Hadoop\nJIRA · Confluence · Agile",
     TEAL),
]

for i, (title, content, col) in enumerate(skills):
    row, ci = divmod(i, 3)
    x = 3   + ci  * 32.5
    y = 20  + row * 39

    # card background
    ck = nid(); reqs += [shape(ck, s3_id, x, y, 30, 37, "ROUND_RECTANGLE"), solid_fill(ck, NAVY2)]
    # coloured header strip
    st = nid(); reqs += [shape(st, s3_id, x, y, 30, 8.5), solid_fill(st, col)]
    # title on strip (dark text for readability)
    label(reqs, s3_id, x+1, y+1.5, 28, 6, title, NAVY, 12, bold=True, alignment="CENTER")
    # content
    label(reqs, s3_id, x+1.5, y+9.5, 27, 26, content, LGRAY, 11)

# ═════════════════════════════════════════════════════════════════════════════
#  SLIDE 4 — CAREER HIGHLIGHTS
# ═════════════════════════════════════════════════════════════════════════════
reqs.append(slide_bg(s4_id, NAVY))
header_band(reqs, s4_id, "Career Highlights", AMBER)

highlights = [
    (LTBLUE,
     "WCB-Alberta  ·  Agentic Medical Assistant (Feb 2024 – Jul 2026)",
     "Serving 2,000+ staff  |  Claim review time reduced by 65%\nLangGraph · LLaMA-4 · Qwen VLM · Databricks Mosaic AI · Apache Kafka"),
    (GREEN,
     "WCB-Alberta  ·  Agentic RAG Pipeline",
     "73% recall on domain-specific answers\nQuery reformulation · Qwen Reranker · Quantized LLaMA 3 · CI/CD Azure DevOps"),
    (AMBER,
     "WCB-Alberta  ·  Premium Audit Risk Model",
     "F1 Score: 68 \u2192 89  (+31%)  |  Production fraud detection\nDatabricks pipelines · Azure DevOps · MLOps best practices"),
    (PINK,
     "University of Alberta  ·  TATEM Entity Matching  (CIKM 2023 · WSDM 2024)",
     "SOTA: Amazon\u2013Google 79.28 \u2192 82.2  |  Walmart\u2013Amazon 87.0 \u2192 90.56\nRoBERTa/GPT · few-shot · novel attribute ranking model"),
]

for i, (col, title, desc) in enumerate(highlights):
    y = 19 + i * 19.5
    accent_bar(reqs, s4_id, 3, y, 0.9, 17, col)
    ck = nid(); reqs += [shape(ck, s4_id, 4.5, y, 92, 17), solid_fill(ck, NAVY2)]
    label(reqs, s4_id,  6.5, y+1.0, 88, 6.5, title, col,   13, bold=True)
    label(reqs, s4_id,  6.5, y+7.5, 88, 9.0, desc,  LGRAY, 12)

# ═════════════════════════════════════════════════════════════════════════════
#  SLIDE 5 — EDUCATION & PUBLICATIONS
# ═════════════════════════════════════════════════════════════════════════════
reqs.append(slide_bg(s5_id, NAVY))
header_band(reqs, s5_id, "Education & Publications", GREEN)

# ── Education (left column) ───────────────────────────────────────────────────
label(reqs, s5_id, 3, 19, 45, 5, "EDUCATION", LTBLUE, 13, bold=True)

edu_items = [
    ("MSc · Computing Science",
     "University of Alberta, Edmonton",
     "GPA 3.84  ·  2020 – 2023",
     "Thesis: E-commerce recommendation & entity matching with LLMs"),
    ("BSc · Computer Engineering",
     "Amirkabir University, Tehran",
     "GPA 3.96  ·  2011 – 2016",
     "Thesis: CNN-based microscope image processing"),
]
for i, (deg, school, detail, thesis) in enumerate(edu_items):
    y = 25 + i * 33
    ck = nid(); reqs += [shape(ck, s5_id, 3, y, 45, 30, "ROUND_RECTANGLE"), solid_fill(ck, NAVY2)]
    lbr = nid(); reqs += [shape(lbr, s5_id, 3, y, 1.5, 30), solid_fill(lbr, LTBLUE)]
    label(reqs, s5_id, 5.5, y+1.5, 41, 6,  deg,    WHITE,  13, bold=True)
    label(reqs, s5_id, 5.5, y+8,   41, 5,  school, LTBLUE, 12)
    label(reqs, s5_id, 5.5, y+13,  41, 5,  detail, AMBER,  11)
    label(reqs, s5_id, 5.5, y+18,  41, 9,  thesis, LGRAY,  11, italic=True)

# ── Publications (right column) ───────────────────────────────────────────────
label(reqs, s5_id, 52, 19, 45, 5, "PUBLICATIONS", GREEN, 13, bold=True)

pubs = [
    ("WSDM 2024",
     "TATTOO: Product Entity Matching\nas Topology Construction"),
    ("CIKM 2023",
     "Product Entity Matching via\nTabular Data"),
    ("NCME 2022",
     "Fine-tuned Word Embedding for\nAutomated Essay Scoring Systems"),
]
for i, (venue, title) in enumerate(pubs):
    y = 25 + i * 23
    ck = nid(); reqs += [shape(ck, s5_id, 52, y, 45, 20, "ROUND_RECTANGLE"), solid_fill(ck, NAVY2)]
    lbr= nid(); reqs += [shape(lbr, s5_id, 52, y, 1.5, 20), solid_fill(lbr, GREEN)]
    label(reqs, s5_id, 55, y+1.5, 13, 6.5, venue,  AMBER,  11, bold=True)
    label(reqs, s5_id, 55, y+8,   40, 11,  title,  LGRAY,  12)

# Closing bar
fb = nid(); reqs += [shape(fb, s5_id, 0, 91, 100, 9), solid_fill(fb, NAVY2)]
line_b = nid(); reqs += [shape(line_b, s5_id, 0, 91, 100, 0.6), solid_fill(line_b, TEAL)]
label(reqs, s5_id, 3, 92, 94, 7,
      "Ready to drive AI innovation at your organization",
      LTBLUE, 17, bold=True, alignment="CENTER")

# ═════════════════════════════════════════════════════════════════════════════
#  Execute all requests in one batch
# ═════════════════════════════════════════════════════════════════════════════
print(f"Sending {len(reqs)} API requests …")
slides_svc.presentations().batchUpdate(
    presentationId=pres_id, body={"requests": reqs}
).execute()

url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
print(f"\n✅  Presentation created successfully!")
print(f"🔗  {url}\n")
