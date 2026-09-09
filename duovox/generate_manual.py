"""Generate the DuoVox User Guide PDF.

Compact, professional layout with a CLICKABLE contents page (internal links +
page numbers), nested PDF outline bookmarks (H1 + H2), and a running footer with
page numbers. Text-only (no screenshots) so it stays small and self-contained,
which lets it be bundled inside the app as well as hosted on the website.

Uses a deterministic TWO-PASS build instead of reportlab's multiBuild (which
oscillates on this content): pass 1 records each section's page number — the
contents page is isolated by a page break, so body pagination is identical
between passes — then pass 2 renders the real contents table with those numbers.

Run:     python duovox/generate_manual.py
Output:  duovox/DuoVox-User-Guide.pdf
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                PageBreak, NextPageTemplate, Table, TableStyle, KeepTogether)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(SCRIPT_DIR, "DuoVox-User-Guide.pdf")

# ── Brand colours (DA Software family purple) ──
BG       = HexColor("#1C1535")
ACCENT   = HexColor("#A580C8")
ACCENTLT = HexColor("#C8A0E8")
GOLD     = HexColor("#FFE088")
TXT      = HexColor("#F0EAF5")
TXT2     = HexColor("#C4B6DA")
WHITE    = HexColor("#FFFFFF")
CARD     = HexColor("#2A2248")
LINE     = HexColor("#3D3560")

S = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=28, leading=32, textColor=WHITE, alignment=TA_CENTER),
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
}


def bullets(items):
    return [Paragraph(f"&bull;&nbsp;&nbsp;{it}", S["bullet"]) for it in items]


def section(*flowables):
    return KeepTogether(list(flowables))


def H1(t): return Paragraph(t, S["H1"])
def H2(t): return Paragraph(t, S["H2"])
def P(t): return Paragraph(t, S["body"])


def tip(text):
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
        self.toc_entries = []

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
    canvas.drawString(18*mm, 10*mm, "DuoVox - User Guide")
    canvas.drawRightString(A4[0]-18*mm, 10*mm, "Page %d" % canvas.getPageNumber())
    canvas.restoreState()


def cover_flowables():
    return [
        Spacer(1, 54*mm),
        Paragraph("DuoVox", S["title"]),
        Spacer(1, 6*mm),
        Paragraph("User Guide", S["coversub"]),
        Spacer(1, 3*mm),
        Paragraph("Real-time transcription &amp; translation &nbsp;&bull;&nbsp; Windows 10 &amp; 11", S["covermeta"]),
        Spacer(1, 96*mm),
        Paragraph("David Arthur Software", S["coversmall"]),
        Paragraph("duovox.net", S["coversmall"]),
        NextPageTemplate("body"),
        PageBreak(),
    ]


def toc_flowables(entries):
    rows = []
    for text, page, key in entries:
        rows.append([
            Paragraph(f'<a href="#{key}" color="#FFE088">{text}</a>', S["tocentry"]),
            Paragraph(f'<a href="#{key}" color="#C4B6DA">{page}</a>', S["tocpage"]),
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
    s += [P("DuoVox transcribes speech in real time and translates it on the fly, so two people who don't "
            "share a language can follow a live, two-way conversation on a single Windows PC. It is built for "
            "interpreters, clinics, classrooms, support desks, businesses and families.")]
    s += [P("As each person speaks, DuoVox shows a live transcript of what was said and, alongside it, a running "
            "translation. It can caption a call or video playing on your computer, or your own microphone.")]
    s += [P("This guide covers everything from your first session to the built-in tools. Use the clickable "
            "Contents page (or your PDF reader's bookmarks panel) to jump to any section.")]

    s += [H1("2. Installation &amp; First Run")]
    s += bullets([
        "<b>Microsoft Store (recommended)</b> &mdash; one-click install, automatic updates, signed by Microsoft. "
        "Find it from duovox.net.",
        "<b>Direct download</b> &mdash; a self-contained installer is also available from the website for offline PCs.",
    ])
    s += [P("On first launch the interface appears in your Windows display language where supported (15 languages "
            "are available); you can change it any time from the globe icon in the toolbar.")]
    s += [tip("DuoVox works straight away on the Free plan with on-device engines &mdash; no account or internet "
              "connection required to get started.")]

    s += [H1("3. The Main Window")]
    s += [P("The caption panels fill the middle of the window. The toolbar across the top holds the menu "
            "(gear icon), the display-language globe, a privacy padlock and the window controls, together with the "
            "everyday session controls &mdash; Topic and Dialect, the two language selectors, Start / Clear, the "
            "layout button and the audio source. A footer shows the version and links. Drag the window by its top "
            "bar; resize from the edges.")]
    s += [H2("The menu")]
    s += [P("Press the gear button (top-right) and a panel slides out with everything grouped into <b>Files</b>, "
            "<b>Current session</b>, <b>Display</b>, <b>Accuracy</b> and <b>Settings &amp; advanced</b> &mdash; "
            "followed further down by Keyboard shortcuts, User guide, Help, Report a problem and About DuoVox. "
            "Under Display, open <b>Appearance</b> to change the theme, buttons, font and caption text size. "
            "Press Esc or click outside the panel to close it.")]

    s += [H1("4. Starting a Session")]
    s += [P("Set your audio source, then press <b>Start</b> (or Ctrl+Alt+S). DuoVox begins listening and filling "
            "the caption panels. Press <b>Stop</b> to end the session.")]
    s += [H2("Choosing the audio source")]
    s += [P("The toolbar shows what DuoVox is currently listening to (for example &ldquo;Listening to: System "
            "audio&rdquo;). Click that button to cycle through the available sources:")]
    s += bullets([
        "<b>System Audio</b> &mdash; captions a call, meeting or video playing on your PC (Teams, Zoom, YouTube, etc.).",
        "<b>Desk Mic</b> or <b>Headset Mic</b> &mdash; captions your own voice through a desk or headset microphone. "
        "The button cycles through all three sources in turn.",
        "If you see a <i>\"no audio\"</i> message, switch the source so it matches where the sound is actually coming from.",
    ])

    s += [H1("5. Primary &amp; Target Languages")]
    s += [P("DuoVox works with two language lanes: a <b>primary</b> language and a <b>target</b> language. Set them "
            "from the two language selectors in the toolbar &mdash; the first picks the primary language, the second "
            "the target (for example, primary English and target Ukrainian). Either lane can be any supported "
            "language, in any direction: DuoVox is fully language-agnostic, so it works for conversations anywhere "
            "in the world.")]
    s += bullets([
        "<b>2-box mode</b> &mdash; shows one speaker and the translation; you can flip the direction with a button.",
        "<b>4-box mode</b> &mdash; shows both speakers transcribed and translated at once, ideal for a true two-way conversation.",
    ])
    s += [P("The globe icon is separate &mdash; it changes the language of DuoVox's own menus and buttons, not the "
            "conversation languages.")]

    s += [H1("6. Topic &amp; Dialect")]
    s += [P("Two selectors in the toolbar help DuoVox recognise the right words for your conversation. Each has an "
            "information (<b>i</b>) button beside it that explains it inside the app.")]
    s += bullets([
        "<b>Topic</b> &mdash; the subject of the conversation (General / Housing / Finance, Medical / Mental Health, "
        "Legal / Immigration / Police, or Education). DuoVox favours that field's specialist vocabulary so terms are "
        "transcribed more accurately.",
        "<b>Dialect</b> &mdash; the region or country, so spelling and word choice match local usage (for example "
        "British versus American English).",
    ])

    s += [H1("7. Translation &amp; Layout")]
    s += [P("Turn <b>Translate</b> on to show translations beside the transcript; turn it off for transcription only. "
            "Toggle between 4 boxes and 2 boxes with the layout button (Ctrl+Alt+R).")]
    s += bullets([
        "<b>Pin on top</b> (menu &gt; Display) keeps the DuoVox window above other apps (Ctrl+Alt+T).",
        "<b>Copy</b> copies the current text; <b>Export this session</b> (menu &gt; Current session) saves .srt "
        "subtitles plus a transcript.",
        "<b>Clear</b> resets the captions and the subtitle clock (Ctrl+Alt+C).",
    ])

    s += [H1("8. Appearance &mdash; Themes, Fonts &amp; Display")]
    s += [P("Open the menu, then <b>Display &gt; Appearance</b>. Pick from a wide range of <b>Themes</b> (the DA "
            "Software purple is the default), choose a <b>Button</b> style, and set the caption <b>Font</b> and "
            "<b>text size</b>. Your choices are remembered between sessions.")]

    s += [H1("9. Plans &amp; Offline Mode")]
    s += [P("DuoVox offers a Free plan and paid plans, and it is designed never to leave you stuck:")]
    s += bullets([
        "<b>Free</b> &mdash; runs fully offline on your device with on-device AI. Unlimited use, no internet needed, supported by ads.",
        "<b>Standard / Professional</b> &mdash; premium online AI for the highest accuracy, with a set number of hours included each month.",
        "<b>Pay-As-You-Go</b> &mdash; buy online AI hours individually, with no subscription.",
    ])
    s += [P("If your internet drops <i>or</i> you reach your monthly hours, DuoVox keeps working in free offline "
            "on-device mode for the rest of the session &mdash; you are never automatically charged. When you reach a "
            "cap you simply choose: buy more hours, continue offline, or end the session.")]
    s += [tip("Offline mode is lower quality than the premium online engines but needs no connection, so a dropped "
              "Wi-Fi signal never interrupts an important conversation.")]

    s += [H1("10. Tools")]
    s += [P("Open the menu (gear icon) for the built-in tools, grouped by area:")]
    s += bullets([
        "<b>Files</b> &mdash; <b>Subtitle a video or audio file</b> (transcribe, and optionally translate, an "
        "existing media file, then export .srt or .vtt) and <b>Translate a document</b> (a TXT, PDF or DOCX file).",
        "<b>Current session</b> &mdash; <b>Export this session</b> saves the live conversation you are running now "
        "as .srt subtitles plus a transcript.",
        "<b>Accuracy</b> &mdash; <b>Glossary</b> and <b>Boost keywords</b> teach DuoVox specialist vocabulary "
        "(medical, legal, technical) so names and terms are recognised accurately.",
        "<b>Settings &amp; advanced</b> &mdash; <b>Download Languages</b> (opens the Language Packs window to get "
        "and manage the on-device models used in offline mode), the audio input device and other advanced options.",
    ])
    s += [H2("Getting subtitles in sync")]
    s += [P("Inside the file-subtitling window there is a <b>Sync offset</b> field that shifts every exported "
            "subtitle in time. If the subtitles appear a little late against your video, enter a negative number of "
            "seconds (for example -0.5) to pull them earlier; enter a positive number if they appear early. Use the "
            "&minus; and + buttons to nudge it, then export .srt or .vtt as usual.")]

    s += [H1("11. Privacy")]
    s += [P("Audio is transcribed in real time. It is not sold, and it is never stored beyond your session. Turn on "
            "<b>Private Mode</b> with the padlock toggle in the toolbar: it clears the captions when you stop and "
            "disables copy and export. Offline modes run entirely on your device with no internet connection at all.")]

    s += [H1("12. Keyboard Shortcuts")]
    s += bullets([
        "<b>Ctrl+Alt+S</b> &mdash; Start / Stop",
        "<b>Ctrl+Alt+C</b> &mdash; Clear (reset subtitle clock)",
        "<b>Ctrl+Alt+E</b> &mdash; Export this session (.srt + transcript)",
        "<b>Ctrl+Alt+T</b> &mdash; Pin on top / Unpin",
        "<b>Ctrl+Alt+R</b> &mdash; Toggle 4 boxes / 2 boxes",
    ])

    s += [H1("13. Support &amp; Contact")]
    s += [P("Questions or feedback are always welcome &mdash; email <b>info@duovox.net</b> and every message is read. "
            "You can also visit duovox.net for the latest news, the privacy policy and the terms of service.")]
    s += [P("The menu also has a <b>Report a problem</b> option. It sends your description of what happened along "
            "with the app version and error counters &mdash; conversation text, translations, audio and your files "
            "are all stripped out &mdash; and reports are deleted automatically after 30 days.")]
    s += [P("If DuoVox helps you, an optional &ldquo;Buy me a coffee&rdquo; keeps a small independent studio going. "
            "Thank you for using DuoVox.")]

    return s


def build():
    # Pass 1: record H1 page numbers. A blank placeholder page stands in for the
    # (single-page) contents so body pagination is identical to pass 2.
    # NOTE: reportlab flowables are stateful, so build a FRESH set for each pass.
    probe = GuideDoc(os.path.join(SCRIPT_DIR, "_probe.pdf"), pagesize=A4,
                     leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    probe.build(cover_flowables() + [PageBreak()] + body_flowables())
    entries = probe.toc_entries
    try:
        os.remove(os.path.join(SCRIPT_DIR, "_probe.pdf"))
    except OSError:
        pass
    # Pass 2: real document with the contents table built from pass-1 page numbers.
    doc = GuideDoc(OUTPUT, pagesize=A4,
                   leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm,
                   title="DuoVox User Guide", author="David Arthur Software")
    doc.build(cover_flowables() + toc_flowables(entries) + body_flowables())
    print("Wrote", OUTPUT)


if __name__ == "__main__":
    build()
