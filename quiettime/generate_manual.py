"""Generate the QuietTime User Guide PDF with updated screenshots."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus.flowables import HRFlowable

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
                         textColor=GOLD, spaceAfter=4*mm, spaceBefore=8*mm),
    "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=12, leading=16,
                         textColor=PURPLE_ACCENT, spaceAfter=3*mm, spaceBefore=6*mm),
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


def add_image(story, filename, max_w=140*mm, max_h=90*mm, caption=None):
    """Add an image centred with optional caption."""
    path = os.path.join(IMG_DIR, filename)
    if not os.path.exists(path):
        story.append(Paragraph(f"[Image not found: {filename}]", styles["body"]))
        return
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        iw, ih = im.size
    ratio = min(max_w / iw, max_h / ih)
    w, h = iw * ratio, ih * ratio
    img = Image(path, width=w, height=h)
    img.hAlign = "CENTER"
    story.append(Spacer(1, 3*mm))
    story.append(img)
    if caption:
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(f"<i>{caption}</i>", ParagraphStyle("Caption", parent=styles["body"],
                               fontSize=8.5, textColor=TEXT_SECONDARY, alignment=TA_CENTER)))
    story.append(Spacer(1, 4*mm))


def hr(story):
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="60%", thickness=0.5, color=PURPLE_ACCENT, spaceAfter=3*mm))


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
        "9. PIN Security",
        "10. Windows-Specific Features",
        "11. Privacy",
        "12. Troubleshooting &amp; FAQ",
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
    story.append(Paragraph("Installation", styles["h2"]))
    story.append(Paragraph(
        "&bull; <b>Android</b> &mdash; Download from Google Play or install the APK directly.", styles["bullet"]))
    story.append(Paragraph(
        "&bull; <b>Windows</b> &mdash; Download from the Microsoft Store or from davidarthur.app/quiettime/.", styles["bullet"]))
    story.append(Paragraph("First Launch", styles["h2"]))
    story.append(Paragraph(
        "When you first open QuietTime, you will be asked to create a 6-digit PIN. "
        "This PIN protects all settings and prevents children from changing the schedule or disabling the app.", styles["body"]))
    add_image(story, "desktop-login.png", max_w=80*mm, max_h=70*mm,
              caption="PIN entry screen (Windows)")
    story.append(Paragraph(
        "<i>Tip: Choose a PIN your child cannot guess. You can change it later from Settings.</i>", styles["tip"]))
    hr(story)

    # ══════════════════════════════════════════
    # 3. THE DASHBOARD
    # ══════════════════════════════════════════
    story.append(Paragraph("3. The Dashboard", styles["h1"]))
    story.append(Paragraph(
        "The dashboard is your control centre. From here you can see the current status, "
        "set schedules, view the schedule overview, and grant extra time.", styles["body"]))
    add_image(story, "dashboard.jpg", max_w=60*mm, max_h=80*mm,
              caption="Dashboard (Android) &mdash; schedules, overview, and extra time")
    story.append(Paragraph("Key controls:", styles["body"]))
    story.append(Paragraph("&bull; <b>Status</b> &mdash; Shows whether QuietTime is active and if a block period is in progress.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Disable / Lock Now</b> &mdash; Temporarily disable QuietTime or start the block immediately.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Weekday &amp; Weekend Schedules</b> &mdash; Set separate start and end times for each.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Schedule Overview</b> &mdash; Visual bars showing when the device will be blocked.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Grant Extra Time</b> &mdash; Give additional minutes during an active block period.", styles["bullet"]))
    add_image(story, "desktop-settings-top.png", max_w=130*mm, max_h=70*mm,
              caption="Dashboard (Windows) &mdash; same features in a wider layout")
    story.append(PageBreak())

    # ══════════════════════════════════════════
    # 4. BLOCK SCREEN THEMES
    # ══════════════════════════════════════════
    story.append(Paragraph("4. Block Screen Themes", styles["h1"]))
    story.append(Paragraph(
        "When the block period starts, the device shows a full-screen animated theme "
        "instead of a harsh lockout message. Five themes are available:", styles["body"]))
    story.append(Paragraph("&bull; <b>Starry Night</b> &mdash; Twinkling stars with a crescent moon", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Dreamy Clouds</b> &mdash; Soft, drifting clouds", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Aquarium</b> &mdash; Underwater scene with gentle movement", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Northern Lights</b> &mdash; Aurora borealis effect", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Fireflies</b> &mdash; Warm glowing fireflies in the dark", styles["bullet"]))
    add_image(story, "desktop-blockscreen.png", max_w=140*mm, max_h=70*mm,
              caption="Starry Night block screen (Windows) with parent controls at the bottom")
    story.append(Paragraph(
        "You can preview themes before selecting them from the Settings page.", styles["body"]))
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
        "time to finish what they are doing. You can set the warning to appear 1, 5, 10, 15, or 30 minutes before bedtime.", styles["body"]))
    story.append(Paragraph(
        "The warning appears as a notification (Android) or overlay (Windows) with a countdown.", styles["body"]))
    add_image(story, "desktop-settings-bottom.png", max_w=130*mm, max_h=70*mm,
              caption="Settings (Windows) &mdash; wind-down warning, themes, lock level, and system options")
    hr(story)

    # ══════════════════════════════════════════
    # 7. PARENT CONTROLS
    # ══════════════════════════════════════════
    story.append(Paragraph("7. Parent Controls", styles["h1"]))
    story.append(Paragraph(
        "Parents have full control during a block period:", styles["body"]))
    story.append(Paragraph("&bull; <b>Grant Extra Time</b> &mdash; Add 15, 30, or 60 minutes to the current block.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Parent Override</b> &mdash; End the block period early with your PIN.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Lock Now</b> &mdash; Start the block immediately, outside the scheduled time.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Disable QuietTime</b> &mdash; Turn off scheduling temporarily.", styles["bullet"]))
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
    story.append(Paragraph("9. PIN Security", styles["h1"]))
    story.append(Paragraph(
        "Your 6-digit PIN protects all settings and controls. Without the PIN, children cannot:", styles["body"]))
    story.append(Paragraph("&bull; Change the schedule", styles["bullet"]))
    story.append(Paragraph("&bull; Disable QuietTime", styles["bullet"]))
    story.append(Paragraph("&bull; Grant extra time", styles["bullet"]))
    story.append(Paragraph("&bull; Override the block", styles["bullet"]))
    story.append(Paragraph("&bull; Change the PIN", styles["bullet"]))
    story.append(Paragraph(
        "You can change your PIN at any time from the Settings page. "
        "If you forget your PIN, you will need to reinstall the app.", styles["body"]))
    hr(story)

    # ══════════════════════════════════════════
    # 10. WINDOWS-SPECIFIC FEATURES
    # ══════════════════════════════════════════
    story.append(Paragraph("10. Windows-Specific Features", styles["h1"]))
    story.append(Paragraph("Lock Level", styles["h2"]))
    story.append(Paragraph(
        "Windows offers three lock levels to control how strictly the block screen is enforced:", styles["body"]))
    story.append(Paragraph("&bull; <b>Gentle</b> &mdash; Shows the block screen but can be dismissed. Good for older children.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Standard</b> &mdash; Fullscreen overlay that requires the PIN to dismiss. Can be bypassed via Task Manager.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>Strict</b> &mdash; Fullscreen overlay that cannot be bypassed without the PIN. Task Manager is blocked.", styles["bullet"]))
    story.append(Paragraph("Start with Windows", styles["h2"]))
    story.append(Paragraph(
        "Enable this option to have QuietTime start automatically when the computer boots. "
        "This ensures the schedule is always active, even if the child restarts the computer.", styles["body"]))
    hr(story)

    # ══════════════════════════════════════════
    # 11. PRIVACY
    # ══════════════════════════════════════════
    story.append(PageBreak())
    story.append(Paragraph("11. Privacy", styles["h1"]))
    story.append(Paragraph(
        "QuietTime is designed with privacy at its core:", styles["body"]))
    story.append(Paragraph("&bull; <b>No accounts</b> &mdash; No sign-up or login required.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>No cloud</b> &mdash; All data stays on your device. Nothing is sent to any server.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>No tracking</b> &mdash; No analytics, no usage data, no telemetry.", styles["bullet"]))
    story.append(Paragraph("&bull; <b>No ads</b> &mdash; No advertisements of any kind.", styles["bullet"]))
    story.append(Paragraph(
        "For full details, see the Privacy Policy at davidarthur.app/quiettime/privacy/.", styles["body"]))
    hr(story)

    # ══════════════════════════════════════════
    # 12. TROUBLESHOOTING & FAQ
    # ══════════════════════════════════════════
    story.append(Paragraph("12. Troubleshooting &amp; FAQ", styles["h1"]))

    faqs = [
        ("Can my child bypass QuietTime?",
         "On Android, QuietTime uses device administrator permissions and accessibility services to prevent bypass. "
         "On Windows, the Strict lock level blocks Task Manager. No method is 100% foolproof, but QuietTime is designed "
         "to make bypassing difficult for children."),
        ("What happens during emergencies?",
         "The emergency call button is always visible on the block screen. Parents can also override or grant extra time at any moment with their PIN."),
        ("What if I forget my PIN?",
         "You will need to reinstall the app. This resets all settings. There is no recovery option because QuietTime does not store data online."),
        ("Does QuietTime use battery?",
         "QuietTime uses minimal battery. It runs a small background service that checks the schedule. The animated block screen only runs during active block periods."),
        ("Can I use different schedules on different days?",
         "Yes. You can set separate times for weekdays and weekends, and choose which days count as weekend days."),
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
    story.append(Paragraph("support@duovox.net", styles["cover_company"]))
    story.append(Spacer(1, 60*mm))
    story.append(Paragraph("&copy; 2026 David Arthur Software. All rights reserved.", styles["footer"]))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"Generated: {OUTPUT}")
    print(f"Pages: {doc.page}")


if __name__ == "__main__":
    build()
