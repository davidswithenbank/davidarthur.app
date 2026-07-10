"""Generate the CCTV Converter User Guide PDF.

Compact, professional layout with a CLICKABLE contents page (internal links +
page numbers), nested PDF outline bookmarks (H1 + H2), and a running footer with
page numbers.

Uses a deterministic TWO-PASS build instead of reportlab's multiBuild (which
oscillates on this content): pass 1 records each section's page number — the
contents page is isolated by a page break, so body pagination is identical
between passes — then pass 2 renders the real contents table with those numbers.

Run:  python cctvconverter/generate_manual.py
Output:  cctvconverter/CCTV-Converter-User-Guide.pdf
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Image, PageBreak, NextPageTemplate, Table, TableStyle, KeepTogether)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "img")
OUTPUT = os.path.join(SCRIPT_DIR, "CCTV-Converter-User-Guide.pdf")

# ── Brand colours ──
BG       = HexColor("#0d0b1a")
ACCENT   = HexColor("#7c3aed")
ACCENTLT = HexColor("#a78bfa")
GOLD     = HexColor("#f59e0b")
TXT      = HexColor("#e8e6f0")
TXT2     = HexColor("#a0a0b8")
WHITE    = HexColor("#ffffff")
CARD     = HexColor("#15122a")
LINE     = HexColor("#241f40")

S = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=27, leading=31, textColor=WHITE, alignment=TA_CENTER),
    "coversub": ParagraphStyle("coversub", fontName="Helvetica", fontSize=15, leading=19, textColor=TXT, alignment=TA_CENTER),
    "covermeta": ParagraphStyle("covermeta", fontName="Helvetica", fontSize=11, leading=15, textColor=TXT2, alignment=TA_CENTER),
    "coversmall": ParagraphStyle("coversmall", fontName="Helvetica", fontSize=10, leading=14, textColor=TXT2, alignment=TA_CENTER),
    "tochdr": ParagraphStyle("tochdr", fontName="Helvetica-Bold", fontSize=15, leading=20, textColor=GOLD, spaceAfter=5*mm),
    "tocentry": ParagraphStyle("tocentry", fontName="Helvetica-Bold", fontSize=10.5, leading=15, textColor=GOLD),
    "tocpage": ParagraphStyle("tocpage", fontName="Helvetica", fontSize=10, leading=15, textColor=TXT2, alignment=TA_RIGHT),
    "H1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=GOLD, spaceBefore=7*mm, spaceAfter=2.5*mm, keepWithNext=1),
    "H2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=ACCENTLT, spaceBefore=4*mm, spaceAfter=1.5*mm, keepWithNext=1),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=TXT, spaceAfter=2.5*mm),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5, leading=13, textColor=TXT, leftIndent=5*mm, spaceAfter=1*mm),
    "tipinner": ParagraphStyle("tipinner", fontName="Helvetica-Oblique", fontSize=9, leading=12.5, textColor=TXT2),
    "cap": ParagraphStyle("cap", fontName="Helvetica-Oblique", fontSize=8, leading=11, textColor=TXT2, alignment=TA_CENTER, spaceAfter=2*mm),
}


def _scaled(path, max_px=1280):
    """Downscale a screenshot for embedding (keeps the PDF small). Falls back to
    the original if PIL isn't available."""
    try:
        from PIL import Image as PILImage
        im = PILImage.open(path)
        if im.width <= max_px:
            return path
        cache = os.path.join(IMG_DIR, "_pdfcache")
        os.makedirs(cache, exist_ok=True)
        out = os.path.join(cache, os.path.splitext(os.path.basename(path))[0] + ".jpg")
        h = int(im.height * max_px / im.width)
        im.convert("RGB").resize((max_px, h), PILImage.LANCZOS).save(out, "JPEG", quality=88, optimize=True)
        return out
    except Exception:
        return path


def img_block(filename, max_w=150*mm, max_h=92*mm, caption=None):
    path = os.path.join(IMG_DIR, filename)
    if not os.path.exists(path):
        return [Paragraph(f"[missing image: {filename}]", S["body"])]
    path = _scaled(path)
    iw, ih = ImageReader(path).getSize()
    r = min(max_w / iw, max_h / ih)
    im = Image(path, width=iw * r, height=ih * r)
    im.hAlign = "CENTER"
    out = [Spacer(1, 1.5*mm), im]
    if caption:
        out += [Spacer(1, 1.5*mm), Paragraph(f"<i>{caption}</i>", S["cap"])]
    out += [Spacer(1, 3*mm)]
    return out


def bullets(items):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{it}", S["bullet"]) for it in items]


def section(*flowables):
    """Keep a whole section on one page (so it's never split when it would fit)."""
    return KeepTogether(list(flowables))


def H1(t): return Paragraph(t, S["H1"])
def H2(t): return Paragraph(t, S["H2"])
def P(t): return Paragraph(t, S["body"])


def tip(text):
    """Callout box rendered as a 1-cell table — tables reserve their padding, so
    the box never overlaps the flowable above it (a Paragraph border does)."""
    inner = Paragraph(f"<b>Tip:</b> {text}", S["tipinner"])
    t = Table([[inner]], colWidths=[174*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD),
        ("BOX", (0, 0), (-1, -1), 0.6, ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 4*mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4*mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3*mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3*mm),
    ]))
    t.spaceBefore = 3*mm
    t.spaceAfter = 3.5*mm
    return t


class GuideDoc(BaseDocTemplate):
    """Bookmarks H1/H2 headings (PDF outline) and records H1 pages for the contents."""
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
        fw = A4[0] - self.leftMargin - self.rightMargin
        fh = A4[1] - self.topMargin - self.bottomMargin
        frame = Frame(self.leftMargin, self.bottomMargin, fw, fh, id="f")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[frame], onPage=_paint_bg),
            PageTemplate(id="body", frames=[frame], onPage=_paint_body),
        ])
        self._k = 0
        self.toc_entries = []   # [(text, page, key), ...] for H1

    def _register(self, fl):
        name = fl.style.name
        if name not in ("H1", "H2"):
            return
        text = fl.getPlainText()
        self._k += 1
        key = "sec%d" % self._k
        level = 0 if name == "H1" else 1
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=(level == 0))
        if level == 0:
            self.toc_entries.append((text, self.page, key))

    def afterFlowable(self, fl):
        # Headings are usually top-level Paragraphs; for image sections the heading
        # lives inside a KeepTogether (so heading + intro + screenshot stay on one
        # page) — register the KeepTogether's leading heading too.
        if isinstance(fl, Paragraph):
            self._register(fl)
        elif isinstance(fl, KeepTogether):
            for child in getattr(fl, "_content", []):
                if isinstance(child, Paragraph) and child.style.name in ("H1", "H2"):
                    self._register(child)


def _paint_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
    canvas.restoreState()


def _paint_body(canvas, doc):
    _paint_bg(canvas, doc)
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(18*mm, 14*mm, A4[0]-18*mm, 14*mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TXT2)
    canvas.drawString(18*mm, 10*mm, "CCTV Converter - User Guide")
    canvas.drawRightString(A4[0]-18*mm, 10*mm, "Page %d" % canvas.getPageNumber())
    canvas.restoreState()


def cover_flowables():
    return [
        Spacer(1, 52*mm),
        Paragraph("CCTV Converter", S["title"]),
        Spacer(1, 6*mm),
        Paragraph("User Guide", S["coversub"]),
        Spacer(1, 3*mm),
        Paragraph("Version 2.0 &nbsp;&bull;&nbsp; Windows 10 &amp; 11", S["covermeta"]),
        Spacer(1, 96*mm),
        Paragraph("David Arthur Software", S["coversmall"]),
        Paragraph("davidarthur.app/cctvconverter", S["coversmall"]),
        NextPageTemplate("body"),
        PageBreak(),
    ]


def toc_flowables(entries):
    rows = []
    for text, page, key in entries:
        rows.append([
            Paragraph(f'<a href="#{key}" color="#f59e0b">{text}</a>', S["tocentry"]),
            Paragraph(f'<a href="#{key}" color="#a0a0b8">{page}</a>', S["tocpage"]),
        ])
    t = Table(rows, colWidths=[150*mm, 24*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    return [Paragraph("Contents", S["tochdr"]), t, PageBreak()]


def body_flowables():
    s = []

    s += [H1("1. Welcome")]
    s += [P("CCTV Converter turns the proprietary recordings produced by Chinese DVRs into standard "
            "MP4 files you can play, edit and share anywhere &mdash; and gives you the tools to review, "
            "enhance, redact and pull highlights from that footage, all on your own PC.")]
    s += [P("It works <b>entirely offline</b>: your footage is read, converted and written locally and "
            "never leaves your machine. There are no accounts, no ads and no tracking.")]
    s += [P("This guide covers everything from a first conversion to the built-in editor, privacy "
            "redaction (faces, number plates or any area), the multi-camera sync view, the continuous day timeline, and automatic motion "
            "highlights. Use the clickable Contents page (or your PDF reader's bookmarks panel) to jump to any section.")]

    s += [H1("2. Installation &amp; First Run")]
    s += bullets([
        "<b>Microsoft Store (recommended)</b> &mdash; one-click install, automatic updates, signed by Microsoft. "
        "Get it at apps.microsoft.com or from davidarthur.app/cctvconverter.",
        "<b>Direct download</b> &mdash; a self-contained installer is also available from the website for offline PCs.",
    ])
    s += [P("The Store version is self-contained: it bundles everything it needs (including its video engine), "
            "so there are no prerequisites to install and no administrator rights are required for normal use.")]
    s += [P("On first launch the interface appears in your Windows display language where supported "
            "(16 languages are available); you can change it any time from the globe icon in the toolbar.")]

    s += [KeepTogether([
              H1("3. The Main Window"),
              P("The window is split into three areas: a <b>file list</b> on the left (your source folders and "
                "the videos inside them), a <b>preview</b> on the right, and an <b>action bar</b> along the bottom."),
          ] + img_block("screen-home.png", caption="The main window: source list and filters on the left, live preview on the right."))]
    s += [H2("Choosing a source and output")]
    s += bullets([
        "<b>Source folder</b> &mdash; drag a folder (or your DVR's SD card) onto the window, or click Browse. "
        "The app walks any date subfolders and lists every video file it finds.",
        "<b>Output folder</b> &mdash; where converted MP4s are written. Both folders are remembered for next time.",
    ])
    s += [H2("Finding the clips you want")]
    s += bullets([
        "Filter by minimum duration, by date, by time of day, or by filename.",
        "Folders with no matching clips collapse out of the way automatically.",
        "Tick individual files, or use <b>Select matching</b> to tick everything that passes the current filter.",
    ])

    s += [H1("4. Converting Footage")]
    s += [P("Tick the files you want and click <b>Convert selected</b>. Where the source is already "
            "MP4-compatible the app does a <i>stream copy</i> &mdash; the video is repackaged without being "
            "re-encoded, so it is instant and bit-identical in quality. Otherwise it re-encodes to clean H.264.")]
    s += bullets([
        "<b>Parallel conversion</b> &mdash; convert up to 8 files at once (set in Settings). A full day of clips finishes in seconds.",
        "<b>Encoder</b> &mdash; Auto, CPU, or a specific GPU (NVIDIA / Intel / AMD). Auto picks the best available and falls back to CPU automatically if a GPU encode fails.",
        "<b>Date/time burn-in</b> &mdash; tick &ldquo;Add timestamp overlay&rdquo; to burn a per-frame clock into the bottom-left of the output, taken from each file's recording time.",
        "<b>Merge</b> &mdash; combine a day's clips, or any selection, into one continuous MP4 in chronological order.",
        "<b>CSV export</b> &mdash; export the file list (name, size, duration, resolution, format, timestamps).",
        "<b>Optional cleanup</b> &mdash; &ldquo;Delete source files after successful conversion&rdquo; reclaims space as you go, with confirmation.",
    ])
    s += [tip("Conversions are cancellable at any point, and partly-written files are cleaned up automatically, "
              "so nothing is left in a bad state.")]

    s += [H1("5. Reviewing &amp; Preview")]
    s += [P("Select any clip to load it into the preview. Play and pause, step frame by frame, change the "
            "playback speed (0.5&times;&ndash;8&times;), adjust volume, and go fullscreen with draggable on-screen controls.")]
    s += bullets([
        "<b>Filmstrip</b> &mdash; a strip of thumbnails above the seek bar lets you scrub by sight; hovering the bar shows a preview pop-up.",
        "<b>Motion heatmap</b> &mdash; after a motion scan, a coloured heatmap along the seek bar shows where the action is; jump straight between events with the prev/next-motion buttons.",
        "<b>Snapshots</b> &mdash; capture any frame as a JPEG or PNG, or copy it straight to the clipboard.",
    ])

    s += [KeepTogether([
              H1("6. The Built-in Editor"),
              P("Select a converted clip and click <b>Edit</b> to open the in-place editor. Edits always export to "
                "a new MP4 &mdash; your original files are never modified &mdash; and a progress bar with a cancel "
                "button shows the export as it runs."),
          ] + img_block("screen-editor.png", caption="The editor: trim, crop, rotate, image adjustments, noise reduction, output size and presets."))]
    s += bullets([
        "<b>Trim</b> &mdash; set the start and end points (down to a single frame) with the range slider or the I / O keyboard shortcuts; mark multiple segments to export separately or merged.",
        "<b>Crop &amp; rotate</b> &mdash; crop to a region of interest or rotate footage recorded sideways.",
        "<b>Image adjustments</b> &mdash; brightness, contrast, saturation, sharpness and gamma, all with a live preview.",
        "<b>One-tap looks</b> &mdash; instant presets (Night, Bright, Clarify, Vivid, Black &amp; White), each shown as a thumbnail so you can preview the effect before applying it.",
        "<b>Noise reduction</b> &mdash; Off / Light / Medium / Strong, to clean up grainy night footage.",
        "<b>Output size &amp; quality</b> &mdash; choose a resolution and quality level for the exported file.",
        "<b>Presets</b> &mdash; save a combination of edit settings and reapply it to other clips in one click.",
    ])

    s += [section(
              H1("7. Privacy &mdash; Hide Faces, Plates &amp; Areas"),
              P("The editor can hide faces, number plates and any other sensitive detail before you share a "
                "clip &mdash; useful when handing footage to a neighbour, an insurer or the public. Everything "
                "runs on your own PC; nothing is uploaded."),
              *bullets([
                  "<b>Detect faces</b> &mdash; automatically finds faces and follows each one as it moves through the clip, drawing a box that tracks it frame by frame.",
                  "<b>Choose who to hide</b> &mdash; click a box to keep that person visible or to hide them; only the faces you pick are redacted.",
                  "<b>Black out, pixelate or blur</b> &mdash; choose how hidden areas look: a solid black box, a coarse mosaic, or a soft blur. The Box size slider grows every automatic box to cover hair or a full head.",
              ]),
          ),
          *img_block("privacy-redact-styles.png",
                     caption="The three redaction styles applied to the same face. Pixelate and blur leave the "
                             "scene readable while making the person unidentifiable."),
          section(
              H2("Hide and track anything else"),
              P("Faces aren't the only thing worth hiding. Turn on <b>Hide areas manually</b> and drag a box "
                "over anything &mdash; a number plate, a bystander, a screen, a document. A drawn box covers "
                "that spot for the whole clip. If the subject moves, click <b>Track this area</b> and the app "
                "follows it automatically: the box glides with the subject in the preview and in the export."),
              *bullets([
                  "<b>Draw where it's clearest</b> &mdash; tracking starts from the exact pixels inside your box, so draw it where the subject is big, sharp and fully visible.",
                  "<b>Check the reported span</b> &mdash; after tracking, the app shows which part of the clip is covered (for example 0:00 to 0:27). A track ends when its subject leaves the frame or is hidden for more than a few seconds.",
                  "<b>Cover other appearances</b> &mdash; if the subject shows up again later in the clip, draw another box there and track again; you can combine as many tracked and static boxes as you need.",
              ]),
          ),
          *img_block("privacy-track-follow.png",
                     caption="Track this area: the box stays locked on the vehicle as it moves through the "
                             "frame &mdash; no manual keyframing."),
          section(
              tip("Automatic detection and tracking are a helpful first pass, not a guarantee &mdash; always "
                  "play the clip back and cover anything left exposed with a manual box before sharing."),
          )]

    s += [section(
              H1("8. Sharing &amp; Exporting"),
              P("Beyond a straight MP4, the editor's <b>Export</b> menu offers ways to share a clip that fit how it will be used."),
              *bullets([
                  "<b>Compress for email</b> &mdash; re-encode to a small target size so a clip fits an email or messaging-app limit.",
                  "<b>Animated GIF</b> &mdash; turn a short moment into a looping GIF for a quick preview or a report.",
                  "<b>Evidence report</b> &mdash; generate a printable PDF that records the source file details and SHA-256 checksums, for a chain-of-custody trail.",
                  "<b>Deinterlace</b> &mdash; smooth the combing produced by older analogue cameras.",
                  "<b>Watermark / case number</b> &mdash; burn a line of text (for example a case reference) into the exported copy.",
              ]),
          )]

    s += [KeepTogether([
              H1("9. Multi-Camera View"),
              P("Tick two or more converted clips and click <b>Multi View</b> to play up to six cameras side by "
                "side on a single shared timeline."),
          ] + img_block("screen-multicam.png", caption="Multi-camera view: up to six cameras on one timeline with per-camera sync offsets."))]
    s += bullets([
        "Nudge each camera's <b>sync offset</b> to line up clocks that have drifted apart.",
        "Rename and rearrange cells, and solo a cell to hear its audio.",
        "<b>Snapshot all</b> cameras at once, or build a combined <b>contact sheet</b>.",
        "<b>Export a synchronized composite</b> video of the whole grid.",
    ])

    s += [section(
              H1("10. Continuous Timeline"),
              P("DVRs chop a day into many short files. Right-click a day and choose <b>Play as timeline</b> to "
                "watch them as one seamless recording instead of opening each file in turn."),
              *bullets([
                  "<b>One scrubber for the whole day</b> &mdash; drag across the joins between files without a gap.",
                  "<b>Jump between motion events</b> across the entire span, even across file boundaries.",
                  "<b>Export any span</b> &mdash; set an in and out point anywhere on the day and export just that stretch, trimmed and joined for you.",
              ]),
          )]

    s += [H1("11. Motion Highlights")]
    s += [P("Select footage and choose <b>Detect motion</b> to have the app scan for movement and extract only "
            "the clips where something happens &mdash; turning hours of recording into a short reel of events.")]
    s += bullets([
        "<b>Sensitivity</b> &mdash; Low / Medium / High controls how much movement counts as an event.",
        "<b>Pre/post-roll</b> &mdash; keep a few seconds before and after each event so nothing is clipped.",
        "<b>Output</b> &mdash; save each event as its own file, or stitch them all into a single highlight reel.",
        "<b>Review</b> &mdash; optionally review and deselect false positives before anything is written.",
        "<b>Inside the editor</b> &mdash; click Detect motion within the editor to mark active stretches as segments, then step between them with the prev/next-motion buttons.",
    ])
    s += [tip("Motion results are cached, so changing the pre/post-roll and re-exporting does not repeat the scan.")]

    s += [H1("12. Watch-Folder Mode")]
    s += [P("Turn on <b>Watch source folder</b> in Settings and the app monitors that folder, automatically "
            "converting new recordings as they appear &mdash; a hands-off workflow for an always-on DVR. It "
            "waits until each file has finished being written before converting, and can pop a notification "
            "when a batch completes.")]

    s += [KeepTogether([
              H1("13. Settings"),
              P("Open <b>Settings</b> from the toolbar to configure conversion and automation. Changes apply immediately."),
          ] + img_block("screen-settings.png", caption="Settings: encoder, output naming, presets, watch-folder and notifications."))]
    s += bullets([
        "<b>Encoder</b> &mdash; Auto, CPU, or a specific GPU.",
        "<b>Filename</b> &mdash; how output files are named (original name, or with a date prefix/suffix).",
        "<b>Parallel</b> &mdash; how many files convert at once (1&ndash;8).",
        "<b>Presets</b> &mdash; save the encoder, concurrency and naming settings as a named preset.",
        "<b>Watch folder</b> &mdash; auto-convert new files, with a file-stability delay.",
        "<b>Notifications</b> &mdash; pop a notification when a batch finishes.",
    ])

    s += [H1("14. Keyboard Shortcuts")]
    rows = [
        ["Space", "Play / pause the preview"],
        ["Left / Right", "Step one frame back / forward"],
        ["I / O", "Set the start (in) / end (out) point in the editor"],
        ["F", "Fullscreen preview"],
        ["M", "Mute / unmute"],
        ["Esc", "Exit fullscreen, or exit the editor"],
    ]
    body = ParagraphStyle("kbd", parent=S["body"], spaceAfter=0)
    keyst = ParagraphStyle("kbdk", parent=body, fontName="Helvetica-Bold", textColor=ACCENTLT)
    trows = [[Paragraph(k, keyst), Paragraph(v, body)] for k, v in rows]
    t = Table(trows, colWidths=[40*mm, 130*mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
    ]))
    s += [t, Spacer(1, 3*mm)]

    s += [section(
        H1("15. Troubleshooting"),
        H2("A file is flagged &ldquo;can't convert&rdquo;"),
        P("A few formats are genuinely undecodable by any third-party tool &mdash; most notably Hikvision "
          "encrypted backups (.crypt), which need Hikvision's own player. Standard Hikvision H.264 backups convert fine."),
        H2("A file won't convert because it's &ldquo;in use&rdquo;"),
        P("Another program (Windows' Films &amp; TV, an Explorer preview, or antivirus) may be holding the file. "
          "Close any preview windows and try again; the app retries automatically for a few seconds."),
        H2("The preview won't play a source file"),
        P("Some raw CCTV formats can't be previewed until converted. Convert the file first, then preview or edit the MP4."),
        H2("Where are my settings and logs?"),
        P("Open <i>About &rarr; Open log/data folder</i>, or browse to %LOCALAPPDATA%\\CctvConverter\\. It holds "
          "your config, the thumbnail cache and an error log &mdash; useful if you ever need to send a support report."),
    )]

    s += [section(
        H1("16. Privacy &amp; Licensing"),
        *bullets([
            "<b>Offline</b> &mdash; your footage is processed locally and never uploaded.",
            "<b>No accounts, no tracking, no ads.</b> The only optional network use is checking for an update when you ask it to.",
            "<b>Local data</b> &mdash; only your folder paths, preferences and caches are stored, under %LOCALAPPDATA%\\CctvConverter\\.",
        ]),
        P("CCTV Converter uses the open-source <b>ffmpeg</b> project (under the GPL) for video processing; the "
          "licence and source details ship with the app. The full Privacy Policy and Terms are at "
          "davidarthur.app/cctvconverter/privacy/ and davidarthur.app/terms/."),
        tip("Converted, edited or timestamped output should not be relied upon as the sole forensic or legal "
            "record &mdash; always retain and verify the original source files for insurance, legal or "
            "law-enforcement use."),
    )]

    s += [section(
        H1("17. Support &amp; Updates"),
        P("The Microsoft Store edition updates automatically; you can also choose <i>About &rarr; Check for "
          "updates</i> at any time. For help, email info@davidarthur.app or see the online guide and FAQ at "
          "davidarthur.app/cctvconverter/help/ and davidarthur.app/cctvconverter/faq/."),
    )]
    s += [Spacer(1, 6*mm),
          Paragraph("&copy; 2026 David Arthur Software. All rights reserved.", S["cap"])]
    return s


def build():
    # PASS 1 — record section page numbers (contents page is a placeholder).
    d1 = GuideDoc(OUTPUT, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                  topMargin=18*mm, bottomMargin=18*mm,
                  title="CCTV Converter — User Guide", author="David Arthur Software")
    story1 = cover_flowables() + [Paragraph("Contents", S["tochdr"]), PageBreak()] + body_flowables()
    d1.build(story1)
    entries = d1.toc_entries

    # PASS 2 — render the real clickable contents with those page numbers.
    d2 = GuideDoc(OUTPUT, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                  topMargin=18*mm, bottomMargin=18*mm,
                  title="CCTV Converter — User Guide", author="David Arthur Software")
    story2 = cover_flowables() + toc_flowables(entries) + body_flowables()
    d2.build(story2)
    print(f"Generated: {OUTPUT}  ({len(entries)} sections)")


if __name__ == "__main__":
    build()
