"""Generate the QuietTime User Guide PDF with updated screenshots."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus.flowables import HRFlowable, Flowable

# ── Paths ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "img")
OUTPUT = os.path.join(SCRIPT_DIR, "QuietTime-User-Guide.pdf")

# ── Colours ──
PURPLE_DARK = HexColor("#0d0b1a")
PURPLE_MID = HexColor("#1a1535")
PURPLE_ACCENT = HexColor("#7c3aed")
GOLD = HexColor("#f59e0b")
TEXT_PRIMARY = HexColor("#e8e6f0")
TEXT_SECONDARY = HexColor("#a0a0b8")
WHITE = HexColor("#ffffff")

# ── Styles ──
styles = {
    "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=20, leading=26,
                            textColor=WHITE, alignment=TA_CENTER, spaceAfter=4*mm),
    "subtitle": ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=11, leading=14,
                               textColor=TEXT_SECONDARY, alignment=TA_CENTER, spaceAfter=6*mm),
    "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=15, leading=20,
                         textColor=GOLD, spaceAfter=4*mm, spaceBefore=8*mm,
                         keepWithNext=1),
    "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=12, leading=16,
                         textColor=PURPLE_ACCENT, spaceAfter=3*mm, spaceBefore=6*mm,
                         keepWithNext=1),
    "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=10, leading=14,
                           textColor=TEXT_PRIMARY, spaceAfter=3*mm),
    "bullet": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=10, leading=14,
                             textColor=TEXT_PRIMARY, leftIndent=6*mm, bulletIndent=2*mm,
                             spaceAfter=1.5*mm),
    "tip": ParagraphStyle("Tip", fontName="Helvetica-Oblique", fontSize=9.5, leading=13,
                          textColor=TEXT_SECONDARY, spaceAfter=4*mm,
                          borderColor=PURPLE_ACCENT, borderWidth=1, borderPadding=3*mm,
                          backColor=HexColor("#12101f")),
    "footer": ParagraphStyle("Footer", fontName="Helvetica", fontSize=8, leading=10,
                             textColor=TEXT_SECONDARY, alignment=TA_CENTER),
    "cover_company": ParagraphStyle("CoverCompany", fontName="Helvetica", fontSize=9,
                                    leading=12, textColor=TEXT_SECONDARY, alignment=TA_CENTER),
}


def image_flowables(filename, max_w=140*mm, max_h=90*mm, caption=None):
    """Build (but don't append) the flowables for an image + caption.

    Caller can either pass straight to story (wrapped in KeepTogether by
    add_image), or prepend extra flowables (a heading, a lead paragraph)
    before wrapping the whole bundle in KeepTogether for tighter binding.
    """
    path = os.path.join(IMG_DIR, filename)
    if not os.path.exists(path):
        return [Paragraph(f"[Image not found: {filename}]", styles["body"])]
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        iw, ih = im.size
    ratio = min(max_w / iw, max_h / ih)
    w, h = iw * ratio, ih * ratio
    img = Image(path, width=w, height=h)
    img.hAlign = "CENTER"
    out = [Spacer(1, 3*mm), img]
    if caption:
        out.append(Spacer(1, 2*mm))
        out.append(Paragraph(f"<i>{caption}</i>", ParagraphStyle("Caption", parent=styles["body"],
                             fontSize=8.5, textColor=TEXT_SECONDARY, alignment=TA_CENTER)))
    out.append(Spacer(1, 4*mm))
    return out


def add_image(story, filename, max_w=140*mm, max_h=90*mm, caption=None, prepend=None):
    """Add an image centred with optional caption.

    Image + caption are wrapped in a KeepTogether so they never split across
    a page break. If `prepend` is provided, those flowables (e.g. a heading
    and a lead paragraph) are placed inside the same KeepTogether — useful
    for tying a section opener to its first image.
    """
    flowables = list(prepend) if prepend else []
    flowables.extend(image_flowables(filename, max_w, max_h, caption))
    story.append(KeepTogether(flowables))


def bullets_block(lead, items):
    """Build (but don't append) the flowables for a lead paragraph + bullets.

    Returned as a flat list so callers can stitch it in alongside a heading
    inside a larger KeepTogether — useful for binding h1 + lead + bullets
    onto the same page."""
    out = [Paragraph(lead, styles["body"])]
    for item in items:
        out.append(Paragraph(f"&bull; {item}", styles["bullet"]))
    return out


def add_bullets(story, lead, items, h1=None, h2=None):
    """Add a lead-in paragraph followed by bullets, kept together on one page.

    Pass h1=... or h2=... to also bundle a heading at the top of the same
    KeepTogether block — this fixes the case where keepWithNext on a heading
    style fails to carry through to a child KeepTogether."""
    block = []
    if h1 is not None:
        block.append(Paragraph(h1, styles["h1"]))
    if h2 is not None:
        block.append(Paragraph(h2, styles["h2"]))
    block.extend(bullets_block(lead, items))
    story.append(KeepTogether(block))


# ── Smart separator ──
class SmartHR(Flowable):
    """A horizontal section separator that disappears at page edges.

    ReportLab passes the remaining height of the current frame to wrap() as
    the `availHeight` argument. We use that to detect:

      - We're at the top of a page: if availHeight is close to a full A4
        usable height (~247mm with default margins), nothing has been placed
        yet on this page, so there's no preceding section to separate from.

      - We're near the bottom of a page: if there's less than `min_room_after`
        left, the following section's heading + first paragraph can't fit on
        this page anyway, so the separator would just orphan at the bottom.

    In both cases the flowable returns zero height and draws nothing.
    """

    keepWithNext = 1  # Stick to the following content where possible.

    def __init__(self, width_pct=0.6, thickness=0.5, color=None,
                 space_before=3*mm, space_after=3*mm,
                 top_of_page_threshold=220*mm, min_room_after=50*mm):
        Flowable.__init__(self)
        self.width_pct = width_pct
        self.thickness = thickness
        self.color = color or PURPLE_ACCENT
        self.spaceBefore = space_before
        self.spaceAfter = space_after
        self.top_of_page_threshold = top_of_page_threshold
        self.min_room_after = min_room_after
        self._suppress = False
        self._availWidth = 0

    def wrap(self, availWidth, availHeight):
        self._availWidth = availWidth
        # Top of page — full frame available means we're the first thing here.
        if availHeight > self.top_of_page_threshold:
            self._suppress = True
            return (availWidth, 0)
        # Near bottom — not enough room for the following section to start.
        if availHeight < self.min_room_after:
            self._suppress = True
            return (availWidth, 0)
        self._suppress = False
        return (availWidth, self.thickness)

    def draw(self):
        if self._suppress:
            return
        c = self.canv
        c.setStrokeColor(self.color)
        c.setLineWidth(self.thickness)
        w = self._availWidth * self.width_pct
        x_center = self._availWidth / 2
        c.line(x_center - w / 2, 0, x_center + w / 2, 0)


def hr(story):
    """Add a smart section separator — auto-suppresses at page top/bottom."""
    story.append(SmartHR())


def build():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )

    def on_page(canvas, doc_):
        canvas.saveState()
        canvas.setFillColor(PURPLE_DARK)
        canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
        canvas.restoreState()

    story = []

    # ══════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════
    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("QuietTime", styles["title"]))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("User Guide", ParagraphStyle("CoverSub", parent=styles["subtitle"],
                            fontSize=14, leading=18, textColor=TEXT_PRIMARY)))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("Version 2.0 &bull; Android &amp; Windows", styles["subtitle"]))
    story.append(Spacer(1, 80*mm))
    story.append(Paragraph("David Arthur Software", styles["cover_company"]))
    story.append(Paragraph("davidarthur.app", styles["cover_company"]))
    story.append(PageBreak())

    # ══════════════════════════════════════════
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════
    story.append(Paragraph("Contents", styles["h1"]))
    toc_items = [
        "1. Welcome",
        "2. Getting Started",
        "3. The Dashboard",
        "4. Block Screen Themes",
        "5. Allowed Apps",
        "6. Wind-Down Warnings",
        "7. Parent Controls",
        "8. Emergency Access",
        "9. PIN &amp; Recovery Password",
        "10. Activity Log",
        "11. Windows-Specific Features",
        "12. Privacy",
        "13. Troubleshooting &amp; FAQ",
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles["body"]))
    story.append(PageBreak())

    # ══════════════════════════════════════════
    # 1. WELCOME
    # ══════════════════════════════════════════
    story.append(Paragraph("1. Welcome", styles["h1"]))
    story.append(Paragraph(
        "QuietTime is a simple screen time control app designed for families. "
        "It lets parents set bedtime schedules that lock the device to a beautiful, "
        "calming screen &mdash; encouraging healthy screen habits without harsh lockouts.", styles["body"]))
    story.append(Paragraph(
        "QuietTime works entirely offline. No accounts, no cloud, no tracking. "
        "Everything stays on your device.", styles["body"]))
    story.append(Paragraph(
        "Available for <b>Android</b> and <b>Windows</b>.", styles["body"]))
    hr(story)

    # ══════════════════════════════════════════
    # 2. GETTING STARTED
    # ══════════════════════════════════════════
    story.append(Paragraph("2. Getting Started", styles["h1"]))
    story.append(KeepTogether([
        Paragraph("Installation", styles["h2"]),
        Paragraph(
            "&bull; <b>Android</b> &mdash; Download from Google Play or install the APK directly.", styles["bullet"]),
        Paragraph(
            "&bull; <b>Windows</b> &mdash; Download from the Microsoft Store or from davidarthur.app/quiettime/.", styles["bullet"]),
    ]))
    add_image(story, "desktop-login.png", max_w=80*mm, max_h=70*mm,
              caption="PIN entry screen (Windows)",
              prepend=[
                  Paragraph("First Launch", styles["h2"]),
                  Paragraph(
                      "When you first open QuietTime, you will be asked to create a 6-digit PIN. "
                      "This PIN protects all settings and prevents children from changing the schedule or disabling the app.", styles["body"]),
              ])
    story.append(Paragraph(
        "<i>Tip: Choose a PIN your child cannot guess. You can change it later from Settings.</i>", styles["tip"]))
    hr(story)

    # ══════════════════════════════════════════
    # 3. THE DASHBOARD
    # ══════════════════════════════════════════
    add_image(story, "dashboard.jpg", max_w=60*mm, max_h=80*mm,
              caption="Dashboard (Android) &mdash; schedule, overview, and extra time",
              prepend=[
                  Paragraph("3. The Dashboard", styles["h1"]),
                  Paragraph(
                      "The dashboard is your control centre. From here you can see the current status, "
                      "set your daily schedule, view the weekly overview, and grant extra time.", styles["body"]),
              ])
    add_bullets(story, "Key controls:", [
        "<b>Status</b> &mdash; Shows whether QuietTime is active and if a block period is in progress.",
        "<b>Enable / Lock Now</b> &mdash; Turn QuietTime on or off, or start the block immediately outside the scheduled time.",
        "<b>Daily Schedule</b> &mdash; Set the Quiet Time window for each day of the week individually. "
        "Each day has its own start time, end time, and on/off toggle &mdash; uncheck a day to skip it entirely.",
        "<b>Schedule Timeline</b> &mdash; Visual bars showing today's and tomorrow's blocked periods.",
        "<b>View Weekly Schedule</b> &mdash; A 7-day grid showing all blocked hours at a glance.",
        "<b>Grant Extra Time</b> &mdash; Give additional minutes during an active block period.",
    ])
    add_image(story, "desktop-settings-top.jpg", max_w=140*mm, max_h=95*mm,
              caption="Settings &mdash; Schedule (Windows) showing daily times, presets, days off and the timeline preview")
    add_bullets(story,
        "<b>Settings Layout (Windows)</b> &mdash; "
        "The Windows Settings window is organised into seven sections accessible from the sidebar on the left:",
        [
            "<b>Schedule</b> &mdash; Daily schedule, presets, days off, timeline preview, and Extra Time.",
            "<b>Notifications</b> &mdash; Wind-down warning and chime sound.",
            "<b>Appearance</b> &mdash; Block screen theme and lock level.",
            "<b>Security</b> &mdash; Change PIN and change recovery password.",
            "<b>System</b> &mdash; Start with Windows.",
            "<b>Activity Log</b> &mdash; Summary, filter, history with CSV export.",
            "<b>About</b> &mdash; Version, links, and support.",
        ])
    story.append(PageBreak())

    # ══════════════════════════════════════════
    # 4. BLOCK SCREEN THEMES
    # ══════════════════════════════════════════
    story.append(KeepTogether([
        Paragraph("4. Block Screen Themes", styles["h1"]),
        Paragraph(
            "When the block period starts, the device shows a full-screen animated theme "
            "instead of a harsh lockout message. Five themes are available:", styles["body"]),
        Paragraph("&bull; <b>Starry Night</b> &mdash; Twinkling stars with a crescent moon", styles["bullet"]),
        Paragraph("&bull; <b>Dreamy Clouds</b> &mdash; Soft, drifting clouds", styles["bullet"]),
        Paragraph("&bull; <b>Aquarium</b> &mdash; Underwater scene with gentle movement", styles["bullet"]),
        Paragraph("&bull; <b>Northern Lights</b> &mdash; Aurora borealis effect", styles["bullet"]),
        Paragraph("&bull; <b>Fireflies</b> &mdash; Warm glowing fireflies in the dark", styles["bullet"]),
    ]))
    add_image(story, "desktop-appearance.jpg", max_w=140*mm, max_h=85*mm,
              caption="Appearance section &mdash; pick a theme and lock level (Windows)")
    story.append(Paragraph(
        "You can preview themes before selecting them from the Settings page.", styles["body"]))
    add_image(story, "desktop-blockscreen.png", max_w=140*mm, max_h=70*mm,
              caption="Starry Night block screen (Windows) with parent controls at the bottom")
    add_image(story, "blockscreen.jpg", max_w=60*mm, max_h=75*mm,
              caption="Starry Night block screen (Android) with allowed apps and emergency call")
    story.append(PageBreak())

    # ══════════════════════════════════════════
    # 5. ALLOWED APPS
    # ══════════════════════════════════════════
    story.append(Paragraph("5. Allowed Apps", styles["h1"]))
    story.append(Paragraph(
        "During a block period, certain apps can remain accessible. This is useful for apps "
        "like alarm clocks, meditation apps, or emergency contacts.", styles["body"]))
    story.append(Paragraph(
        "On <b>Android</b>, allowed apps appear as icons on the block screen. Tap one to open it. "
        "On <b>Windows</b>, allowed apps can bypass the lock overlay.", styles["body"]))
    story.append(Paragraph(
        "<i>Tip: Keep the allowed list short. The purpose of QuietTime is to reduce screen time, "
        "so only allow apps that are genuinely needed at bedtime.</i>", styles["tip"]))
    hr(story)

    # ══════════════════════════════════════════
    # 6. WIND-DOWN WARNINGS
    # ══════════════════════════════════════════
    story.append(Paragraph("6. Wind-Down Warnings", styles["h1"]))
    story.append(Paragraph(
        "QuietTime can show a warning before the block period starts, giving children "
        "time to finish what they are doing. You can set the warning to appear 5, 10, 15, or 30 minutes before bedtime.", styles["body"]))
    story.append(Paragraph(
        "Once wind-down begins, QuietTime shows a series of system tray notifications counting down to bedtime "
        "(at 30, 15, 10, 5, 2 and 1 minute remaining, depending on your warning time).", styles["body"]))

    story.append(Paragraph("Chime Sounds (Windows)", styles["h2"]))
    story.append(Paragraph(
        "On Windows, you can choose a chime sound that plays alongside the wind-down notifications. "
        "Chimes are intentionally gentle and non-startling. To keep things polite, chimes only play at "
        "the start of the wind-down period and again at the 5 and 1 minute marks &mdash; not on every "
        "notification.", styles["body"]))
    add_bullets(story, "Eight chime sounds are included:", [
        "<b>Bell</b> &mdash; Classic single bell tone",
        "<b>Soft Bell</b> &mdash; Warm, low bell with a longer decay",
        "<b>Chime</b> &mdash; Two-note descending doorbell",
        "<b>Music Box</b> &mdash; Three rising notes",
        "<b>Wind Chime</b> &mdash; Three bell tones with staggered timing",
        "<b>Twinkle</b> &mdash; Bright ascending arpeggio",
        "<b>Harp</b> &mdash; Gentle descending cascade",
        "<b>Tone</b> &mdash; Short, simple beep",
    ])
    story.append(Paragraph(
        "Selecting <b>Random</b> tells QuietTime to choose a different chime each time, avoiding repeats. "
        "Selecting <b>None</b> disables chimes entirely while keeping the visual notifications. "
        "Use the &lsquo;Preview&rsquo; button in Settings to listen to each chime before choosing.", styles["body"]))

    add_image(story, "desktop-notifications.jpg", max_w=140*mm, max_h=95*mm,
              caption="Notifications section (Windows) &mdash; warning time and chime sound, including the Random option")
    hr(story)

    # ══════════════════════════════════════════
    # 7. PARENT CONTROLS
    # ══════════════════════════════════════════
    add_bullets(story, "Parents have full control during a block period:", [
        "<b>Grant Extra Time</b> &mdash; Add 15 minutes, 30 minutes, 1 hour, or 2 hours to the current block.",
        "<b>Parent Override</b> &mdash; End the block period early with your PIN.",
        "<b>Lock Now</b> &mdash; Start the block immediately, outside the scheduled time.",
        "<b>Disable QuietTime</b> &mdash; Turn off scheduling temporarily.",
    ], h1="7. Parent Controls")
    story.append(Paragraph(
        "All actions require PIN entry to prevent children from bypassing the controls.", styles["body"]))
    hr(story)

    # ══════════════════════════════════════════
    # 8. EMERGENCY ACCESS
    # ══════════════════════════════════════════
    story.append(Paragraph("8. Emergency Access", styles["h1"]))
    story.append(Paragraph(
        "The emergency call button is always visible on the block screen, even during an active block. "
        "On Android, tapping it opens the phone dialler. Parents can also set a specific emergency "
        "contact number that children can call directly from the block screen.", styles["body"]))
    story.append(Paragraph(
        "<i>Tip: Set an emergency contact number in Settings so your child can always reach you.</i>", styles["tip"]))
    hr(story)

    # ══════════════════════════════════════════
    # 9. PIN SECURITY
    # ══════════════════════════════════════════
    add_bullets(story,
        "Your 6-digit PIN protects all settings and controls. Without the PIN, children cannot:",
        [
            "Change the schedule",
            "Disable QuietTime",
            "Grant extra time",
            "Override the block",
            "Change the PIN",
        ], h1="9. PIN &amp; Recovery Password")
    story.append(Paragraph(
        "You can change your PIN at any time from the Settings page.", styles["body"]))
    story.append(Paragraph("Recovery Password", styles["h2"]))
    story.append(Paragraph(
        "QuietTime allows you to set a recovery password as a backup. If you forget your PIN, "
        "you can use the recovery password to reset it.", styles["body"]))
    story.append(Paragraph(
        "If you lose both your PIN and recovery password, the only way to regain access is to "
        "clear the app's data or reinstall, which will remove all settings and schedules.", styles["body"]))
    story.append(Paragraph(
        "<i>Tip: Write your recovery password down and keep it somewhere safe.</i>", styles["tip"]))
    add_image(story, "desktop-security.jpg", max_w=140*mm, max_h=80*mm,
              caption="Security section (Windows) &mdash; change PIN and change recovery password")
    hr(story)

    # ══════════════════════════════════════════
    # 10. ACTIVITY LOG
    # ══════════════════════════════════════════
    add_image(story, "desktop-activitylog.jpg", max_w=140*mm, max_h=85*mm,
              caption="Activity Log (Windows) &mdash; 7-day summary, filter, colour-coded entries grouped by day, with Export and PIN-protected Clear",
              prepend=[
                  Paragraph("10. Activity Log", styles["h1"]),
                  Paragraph(
                      "QuietTime keeps a local activity log on your device so you can review how the app "
                      "has been used. Open it from the <b>Activity Log</b> entry in the Settings sidebar. "
                      "The log is stored only on your device and is never sent anywhere.", styles["body"]),
              ])

    add_bullets(story, "<b>Events recorded:</b>", [
        "Block period start and end times (paired into a single &lsquo;block period&rsquo; row with duration)",
        "Parent overrides used",
        "Extra time granted",
        "Schedule preset applied, saved, or deleted",
        "Day off added or removed",
        "Settings changes",
        "PIN or recovery password changed",
        "Lock level, theme, wind-down warning, or language changed",
        "App started and shut down",
    ])

    story.append(Paragraph("Summary card", styles["h2"]))
    story.append(Paragraph(
        "At the top of the log you see at-a-glance counters for the last 7 days: how many "
        "block periods completed, how many overrides were used, and how many minutes of extra "
        "time were granted. Overrides and extra time are shown in accent colour so they stand "
        "out from routine activity.", styles["body"]))

    story.append(Paragraph("Filter", styles["h2"]))
    add_bullets(story,
        "Use the filter dropdown to narrow the list to a single category:",
        [
            "<b>All events</b> &mdash; everything",
            "<b>Block periods</b> &mdash; routine quiet-time blocks",
            "<b>Overrides &amp; extras</b> &mdash; parent overrides and granted extra time",
            "<b>Schedule changes</b> &mdash; presets, days off, schedule edits",
            "<b>Security changes</b> &mdash; PIN, recovery password, lock level",
            "<b>System &amp; app</b> &mdash; theme, wind-down, language, app start/shutdown",
        ])

    story.append(Paragraph("Visual cues", styles["h2"]))
    add_bullets(story, "Each entry has a coloured stripe on its left edge so you can scan the log quickly:", [
        "<b>Red</b> &mdash; overrides and extensions (worth knowing about)",
        "<b>Gold</b> &mdash; security changes (PIN, recovery, lock level)",
        "<b>Purple</b> &mdash; schedule changes",
        "<b>Neutral grey</b> &mdash; routine block periods",
        "<b>Dim grey</b> &mdash; background system events",
    ])
    story.append(Paragraph(
        "Entries are grouped by day with <b>Today / Yesterday</b> headers so you can find "
        "recent activity at a glance.", styles["body"]))

    story.append(Paragraph("Export to CSV", styles["h2"]))
    story.append(Paragraph(
        "Click <b>Export…</b> to save the log as a CSV file (opens in Excel, Numbers, "
        "or any spreadsheet app). Useful for sharing with a co-parent, archiving before "
        "a clear, or reviewing patterns over a longer period.", styles["body"]))

    story.append(Paragraph("Clear log (PIN required)", styles["h2"]))
    story.append(Paragraph(
        "Clearing the log is destructive and irreversible, so QuietTime asks for your PIN "
        "every time &mdash; even though you've already entered it to open Settings. This "
        "protects the audit trail if you walk away from an open Settings window.", styles["body"]))
    story.append(Paragraph(
        "<i>Tip: Export the log to CSV before clearing if you'd like to keep a record.</i>",
        styles["tip"]))

    hr(story)

    # ══════════════════════════════════════════
    # 10. WINDOWS-SPECIFIC FEATURES
    # ══════════════════════════════════════════
    add_bullets(story,
        "Windows offers three lock levels to control how strictly the block screen is enforced:",
        [
            "<b>Gentle</b> &mdash; Shows the block screen but can be dismissed. Good for older children.",
            "<b>Standard</b> &mdash; Fullscreen overlay that requires the PIN to dismiss. Can be bypassed via Task Manager.",
            "<b>Strict</b> &mdash; Fullscreen overlay that cannot be bypassed without the PIN. Task Manager is blocked.",
        ], h1="11. Windows-Specific Features", h2="Lock Level")
    story.append(Paragraph("Start with Windows", styles["h2"]))
    story.append(Paragraph(
        "Enable this option to have QuietTime start automatically when the computer boots. "
        "This ensures the schedule is always active, even if the child restarts the computer.", styles["body"]))
    hr(story)

    # ══════════════════════════════════════════
    # 11. PRIVACY — keep together so it doesn't split across pages
    # ══════════════════════════════════════════
    privacy_block = [
        Paragraph("12. Privacy", styles["h1"]),
        Paragraph("QuietTime is designed with privacy at its core:", styles["body"]),
        Paragraph("&bull; <b>No accounts</b> &mdash; No sign-up or login required.", styles["bullet"]),
        Paragraph("&bull; <b>No cloud</b> &mdash; All data stays on your device. Nothing is sent to any server.", styles["bullet"]),
        Paragraph("&bull; <b>No tracking</b> &mdash; No analytics, no usage data, no telemetry.", styles["bullet"]),
        Paragraph("&bull; <b>No ads</b> &mdash; No advertisements of any kind.", styles["bullet"]),
        Paragraph("For full details, see the Privacy Policy at davidarthur.app/quiettime/privacy/.", styles["body"]),
    ]
    story.append(KeepTogether(privacy_block))
    hr(story)

    # ══════════════════════════════════════════
    # 12. TROUBLESHOOTING & FAQ
    # ══════════════════════════════════════════
    story.append(Paragraph("13. Troubleshooting &amp; FAQ", styles["h1"]))

    faqs = [
        ("Can my child bypass QuietTime?",
         "On Android, QuietTime uses device administrator permissions and accessibility services to prevent bypass. "
         "On Windows, the Strict lock level blocks Task Manager. No method is 100% foolproof, but QuietTime is designed "
         "to make bypassing difficult for children."),
        ("What happens during emergencies?",
         "The emergency call button is always visible on the block screen. Parents can also override or grant extra time at any moment with their PIN."),
        ("What if I forget my PIN?",
         "Use your recovery password to reset it. If you've lost both your PIN and recovery password, "
         "you'll need to clear the app's data or reinstall, which will remove all settings and schedules. "
         "We recommend writing your recovery password down somewhere safe."),
        ("Does QuietTime use battery?",
         "QuietTime uses minimal battery. It runs a small background service that checks the schedule. The animated block screen only runs during active block periods."),
        ("Can I use different schedules on different days?",
         "Yes. From version 2.0 onwards each day of the week has its own start time, end time and on/off toggle, "
         "so you can set Monday's bedtime later than Friday's, give Saturday a lie-in, or skip Sunday entirely. "
         "You can also save the whole week as a preset (e.g. \"School Term\" or \"Holidays\") and switch between them with one click."),
    ]

    for q, a in faqs:
        story.append(Paragraph(f"<b>Q: {q}</b>", styles["body"]))
        story.append(Paragraph(f"A: {a}", styles["body"]))
        story.append(Spacer(1, 3*mm))

    story.append(PageBreak())

    # ══════════════════════════════════════════
    # BACK COVER
    # ══════════════════════════════════════════
    story.append(Spacer(1, 80*mm))
    story.append(Paragraph("QuietTime", ParagraphStyle("BackTitle", parent=styles["title"], fontSize=18)))
    story.append(Spacer(1, 12*mm))
    story.append(Paragraph("Simple screen time control that respects your family's privacy.", styles["subtitle"]))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph("davidarthur.app/quiettime/", styles["cover_company"]))
    story.append(Paragraph("info@davidarthur.app", styles["cover_company"]))
    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("&copy; 2026 David Arthur Software. All rights reserved.", styles["footer"]))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Generated: {OUTPUT}")
    print(f"Pages: {doc.page}")


if __name__ == "__main__":
    build()
