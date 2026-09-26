"""
email_actions.py - GHL Conversations API email sends for the JHP workflow runner.

Ported from R.H.L Boudoir (rhl-boudoir/email_actions.py). Two handlers, both
riding GHL's POST /conversations/messages:
  - action_send_email          - transactional 1:1 emails
  - action_send_questionnaire  - email inviting the client to fill a form,
                                 embedding {{ form.url }} from action_config.form_url

Both respect the contact's Email DND flag in GHL, which GHL enforces itself on
every send. For test contacts toggle DND off temporarily.

MARKETING email additionally checks email_optouts before sending -- see
is_suppressed() -- and carries the CAN-SPAM footer. Transactional email does
neither, because an unsubscribe is not a request to stop hearing about your own
booked session. WHICH IS WHICH IS DECIDED BY MARKETING_WORKFLOWS BELOW, and the
default is transactional.

Reads secret RHL... -> here GHL_API_KEY (jhp declared_secret 'ghl_api_key').
"""
import os
import logging
import re
from urllib.parse import quote
import requests

log = logging.getLogger('workflow_runner.email')

GHL_V2_BASE = "https://services.leadconnectorhq.com"

# Brand palette - JHP Boudoir (warm gold on cream).
BRAND_LINK = '#9a7b4f'
BUTTON_BG = '#9a7b4f'
BUTTON_FG = '#ffffff'
BLOCKQUOTE_BG = '#faf7f2'
HR_COLOR = '#e7e0d6'
HEADING_COLOR = '#1a1714'
PAGE_BG = '#f4efe7'
CONTAINER_BG = '#ffffff'
CONTAINER_PADDING = '36px 32px'

# Brand logo - the hosted JHP Boudoir mark (the same Google-hosted asset used on
# the landing pages). Rendered as a centered header at the top of every email.
# Fetched at 2x (=w320) for retina sharpness and displayed at LOGO_WIDTH px.
LOGO_URL = 'https://lh3.googleusercontent.com/d/1BJq9-2dGYZbWbP73GM6s1QGUimAqdqhb=w320'
LOGO_WIDTH = '150'

# ---------------------------------------------------------------------------
# The CAN-SPAM footer (added 2026-09-26, Jessica's address supplied the same day)
#
# Commercial email needs an accurate sender, a physical postal address and a
# working opt-out honoured promptly. Before this, not one of the thirty-seven
# email steps on the tenant carried either the address or an unsubscribe.
#
# ONLY MARKETING EMAIL GETS THIS FOOTER, and that is a safety decision, not a
# legal shortcut. Transactional and relationship email -- a session
# confirmation, a contract, an image reveal -- is exempt from the opt-out
# requirement, and inviting a booked client to unsubscribe would be actively
# harmful: GHL's Email DND is ACCOUNT-WIDE, so a client who used it would stop
# receiving her own session emails as well. Hence an explicit allowlist and no
# footer by default. A NEW MARKETING SEQUENCE MUST BE ADDED TO IT.
STUDIO_NAME = 'JHP Boudoir'
STUDIO_ADDRESS = '11811 Main Street, Centertown, MO 65023'
UNSUB_BASE = 'https://pages.scalogy.com/jhpboudoir1/unsubscribe/'

MARKETING_WORKFLOWS = {
    'website_inquiry_2027',
    'promo_inquiry_nurture',
    'referral_program',
}

# NOT in the set, and each for a reason worth keeping written down:
#   boudoir_giveaway_lead_capture  a paid winner being walked through picking a
#                                  date, signing and setting up her plan. That is
#                                  a booking email, exactly like a confirmation.
#   emc_prepay_reminders           paid, setting up her plan
#   promo_booking_reminders        paid, finishing her booking
#   image_reveal / reschedule      her own session and her own images
# Jessica's rule, 26 September: booking emails do not carry an unsubscribe.

# Why she is hearing from us, per sequence. A woman six months past an inquiry
# genuinely may not remember, and saying so plainly is the cheapest thing there
# is for keeping a marked-as-spam click from happening.
WHY = {
    'website_inquiry_2027': ('You are getting this because you asked for the '
                            'Session Guide at jhpboudoir.com.'),
    'promo_inquiry_nurture': ('You are getting this because you asked about the '
                             'last-minute session sale at jhpboudoir.com.'),
    'referral_program': ('You are getting this because you have been '
                        'photographed at JHP Boudoir.'),
}
WHY_DEFAULT = 'You are getting this because you contacted JHP Boudoir.'

# ---------------------------------------------------------------------------
# SMS compliance (added 2026-09-26)
#
# A marketing text needs three things an email does not, and all three are
# enforced in action_send_sms rather than trusted to the copy:
#
#   1. PRIOR EXPRESS WRITTEN CONSENT. The /contact consent box writes
#      site_leads.sms_consent, enroll_website_inquiry stamps it onto the
#      enrollment, and a marketing text without it is refused here. TCPA damages
#      are per message, so this is the expensive one to get wrong -- which is why
#      the default is NO and an absent flag is not consent.
#   2. QUIET HOURS. A marketing text outside 8am-9pm in the recipient's local
#      time is a violation on its own. Her clients are Missouri, so the window is
#      America/Chicago and tightened to 9am-8pm: a text from a boudoir studio at
#      five past eight in the morning is legal and still wrong.
#   3. AN OPT-OUT THAT WORKS. GHL processes an inbound STOP itself and sets SMS
#      DND, which it then enforces on every send; the website-inquiry stopgate
#      also cancels the whole sequence on any inbound message, so a STOP ends the
#      emails too. The copy carries the STOP wording; see the builder.
#
# Transactional texts -- your session is tomorrow, your images are ready -- are
# not gated by any of this, exactly as they are not gated by the email footer.
SMS_QUIET_START = 9    # inclusive, America/Chicago
SMS_QUIET_END = 20     # exclusive, so the last text can go at 19:59
SMS_TZ = 'America/Chicago'


def sms_blocked_reason(ctx):
    """Why a MARKETING text must not be sent right now, or None if it may be.

    Returns a short string so the caller can log the actual reason: 'no consent'
    and 'quiet hours' are the same non-event in the log otherwise, and they want
    very different fixes.
    """
    wf = (ctx or {}).get('workflow')
    if wf not in MARKETING_WORKFLOWS:
        return None
    enr_ctx = ((ctx or {}).get('enrollment') or {}).get('context') or {}
    if not isinstance(enr_ctx, dict):
        enr_ctx = {}
    if enr_ctx.get('sms_consent') is not True:
        return 'no SMS consent on this enrollment'
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        hour = datetime.now(ZoneInfo(SMS_TZ)).hour
    except Exception as e:
        # Cannot establish the local hour -> do not send. The one thing worse
        # than a delayed text is a 3am one.
        return f'local time unavailable ({e})'
    if hour < SMS_QUIET_START or hour >= SMS_QUIET_END:
        return (f'quiet hours ({hour:02d}:00 {SMS_TZ}, window '
                f'{SMS_QUIET_START:02d}-{SMS_QUIET_END:02d})')
    return None


def is_suppressed(conn, ctx):
    """True if this contact has unsubscribed from marketing email.

    THIS IS THE THING THAT ACTUALLY HONOURS AN OPT-OUT. GHL's Email DND would
    have done it too, but account-wide -- it blocks transactional email as well,
    so a woman who unsubscribed from a nurture sequence and later booked would
    silently stop receiving her own confirmation and contract. So the opt-out
    lives in email_optouts and is enforced here, on marketing sends only.

    Fails OPEN on a database error, which is the uncomfortable choice and the
    right one: the alternative is a transient error silently stopping every
    marketing email on the tenant. The ingest also cancels the contact's
    enrollments outright, so a send would have to survive that as well to reach
    somebody who opted out.
    """
    c = (ctx or {}).get('contact') or {}
    cid, email = c.get('id'), c.get('email')
    if not cid and not email:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM email_optouts WHERE "
                "(%s <> '' AND ghl_contact_id = %s) OR "
                "(%s <> '' AND lower(email) = lower(%s)) LIMIT 1",
                (cid or '', cid or '', email or '', email or ''))
            return cur.fetchone() is not None
    except Exception as e:
        log.warning(f"  could not check the opt-out list, allowing the send: {e}")
        return False


def _legal_footer_html(ctx):
    """The compliance footer, or '' when the sequence is transactional.

    Set apart from the letter by a rule and small grey type, because it is
    housekeeping rather than something she is being asked to read.
    """
    wf = (ctx or {}).get('workflow')
    if wf not in MARKETING_WORKFLOWS:
        return ''
    c = (ctx or {}).get('contact') or {}
    parts = []
    if c.get('id'):
        parts.append('c=' + quote(str(c['id'])))
    if c.get('email'):
        parts.append('e=' + quote(str(c['email'])))
    url = UNSUB_BASE + ('?' + '&'.join(parts) if parts else '')
    why = WHY.get(wf, WHY_DEFAULT)
    return (
        f'<tr><td style="padding: 0 32px 30px 32px;">'
        f'<div style="border-top: 1px solid {HR_COLOR}; padding-top: 18px; '
        f'font-size: 12px; line-height: 1.65; color: #8c8175;">'
        f'<div style="margin-bottom: 8px;">{why}</div>'
        f'<div style="margin-bottom: 8px;"><strong style="color:#6b6259">'
        f'{STUDIO_NAME}</strong><br>{STUDIO_ADDRESS}</div>'
        f'<div><a href="{url}" style="color: #8c8175; '
        f'text-decoration: underline;">Unsubscribe from these emails</a></div>'
        f'</div></td></tr>'
    )


def _hdrs():
    key = os.environ.get('GHL_API_KEY')
    if not key:
        raise RuntimeError("GHL_API_KEY not declared on runner")
    return {
        "Authorization": f"Bearer {key}",
        "Version": "2021-07-28",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _ghl_post(path, body):
    url = f"{GHL_V2_BASE}{path}"
    r = requests.post(url, headers=_hdrs(), json=body, timeout=30)
    if not r.ok:
        log.warning(f"  GHL POST {path} -> {r.status_code}: {r.text[:400]}")
    r.raise_for_status()
    return r.json()


def _logo_header_html():
    """Centered JHP Boudoir logo header row, divided from the body below."""
    return (
        f'<tr><td style="padding: 32px 32px 22px 32px; text-align: center; '
        f'border-bottom: 1px solid {HR_COLOR};">'
        f'<img src="{LOGO_URL}" alt="JHP Boudoir" width="{LOGO_WIDTH}" '
        f'style="width: {LOGO_WIDTH}px; max-width: 55%; height: auto; '
        f'display: inline-block; border: 0; outline: none; text-decoration: none;" />'
        f'</td></tr>'
    )


def _wrap_html(body_html, footer_html=''):
    """Wrap a ready HTML body in the branded 600px container on cream, with the
    JHP Boudoir logo as a centered header at the top of every email and, for
    marketing sends, the compliance footer inside the same card."""
    return (
        f'<div style="background: {PAGE_BG}; padding: 24px 12px; '
        f'font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', '
        f'Helvetica, Arial, sans-serif;">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'style="max-width: 600px; margin: 0 auto; background: {CONTAINER_BG}; '
        f'border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">'
        f'{_logo_header_html()}'
        f'<tr><td style="padding: {CONTAINER_PADDING};">{body_html}</td></tr>'
        f'{footer_html}'
        f'</table></div>'
    )


def _md_to_html(md, footer_html=''):
    """Markdown -> email-safe HTML. Supports headings, bold/italic, blockquote,
    hr, inline + standalone links (standalone => centered CTA button), images,
    and auto-linked plain URLs. Wraps in a 600px white container on cream."""
    if not md:
        return ''

    # Body already HTML (GHL-formatted workflow emails)? Pass it through as-is
    # inside the branded container. Do NOT markdown-process it — that would
    # escape the tags and show raw HTML to the recipient.
    if re.search(r'<(p|div|h[1-6]|ul|ol|li|table|tr|td|a|br|strong|em|img|span)\b', md, re.I):
        return _wrap_html(md, footer_html)

    placeholders = {}
    counter = [0]

    def ph(html):
        key = f"XMDPHX{counter[0]}XMDPHX"
        placeholders[key] = html
        counter[0] += 1
        return key

    lines = md.split('\n')
    out_lines = []
    blockquote_buffer = []

    def flush_blockquote():
        if not blockquote_buffer:
            return
        content = '<br>'.join(blockquote_buffer)
        out_lines.append(ph(
            f'<blockquote style="border-left: 3px solid {BRAND_LINK}; '
            f'padding: 12px 16px; margin: 20px 0; color: #555; '
            f'font-style: italic; background: {BLOCKQUOTE_BG}; '
            f'border-radius: 0 4px 4px 0;">{content}</blockquote>'
        ))
        blockquote_buffer.clear()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('> '):
            blockquote_buffer.append(stripped[2:])
            continue
        if stripped == '>':
            blockquote_buffer.append('')
            continue
        if blockquote_buffer:
            flush_blockquote()
        if stripped == '---':
            out_lines.append(ph(
                f'<hr style="border: none; border-top: 1px solid {HR_COLOR}; '
                f'margin: 28px 0;">'
            ))
            continue
        m = re.fullmatch(r'(#{2,3})\s+(.+)', stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2)
            sizes = {2: '22px', 3: '17px'}
            margins = {2: '32px 0 16px 0', 3: '24px 0 12px 0'}
            out_lines.append(ph(
                f'<h{level} style="font-family: Georgia, serif; '
                f'font-size: {sizes[level]}; color: {HEADING_COLOR}; '
                f'margin: {margins[level]}; font-weight: 600; letter-spacing: 0.3px;">'
                f'{text}</h{level}>'
            ))
            continue
        m = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', stripped)
        if m:
            alt, url = m.group(1), m.group(2)
            alt_safe = (alt.replace('&', '&amp;').replace('<', '&lt;')
                        .replace('>', '&gt;').replace('"', '&quot;'))
            # The width ATTRIBUTE is not decoration: Outlook renders through
            # Word, which ignores max-width and would draw a 1600px frame at
            # its native size and blow the 600px card apart. 536 = the card's
            # 600 less its 32px of padding either side. No live sequence used a
            # markdown image before this (checked 2026-09-26), so adding it
            # cannot change an email already going out.
            out_lines.append(ph(
                f'<div style="text-align: center; margin: 24px 0;">'
                f'<img src="{url}" alt="{alt_safe}" width="536" '
                f'style="width: 100%; max-width: 536px; height: auto; '
                f'display: block; margin: 0 auto; border-radius: 4px;" /></div>'
            ))
            continue
        m = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', stripped)
        if m:
            text, url = m.group(1), m.group(2)
            out_lines.append(ph(
                f'<div style="text-align: center; margin: 28px 0;">'
                f'<a href="{url}" style="display: inline-block; '
                f'background: {BUTTON_BG}; color: {BUTTON_FG}; '
                f'padding: 14px 36px; text-decoration: none; '
                f'border-radius: 2px; font-size: 13px; letter-spacing: 1.2px; '
                f'text-transform: uppercase; font-weight: 500;">{text}</a></div>'
            ))
            continue
        line_with_imgs = re.sub(
            r'!\[([^\]]*)\]\(([^)]+)\)',
            lambda mm: ph(
                f'<img src="{mm.group(2)}" alt="'
                f'{(mm.group(1) or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace(chr(34), "&quot;")}" '
                f'style="max-width: 100%; height: auto; vertical-align: middle; '
                f'border-radius: 4px;" />'
            ),
            line
        )
        line_processed = re.sub(
            r'\[([^\]]+)\]\(([^)]+)\)',
            lambda mm: ph(
                f'<a href="{mm.group(2)}" style="color: {BRAND_LINK}; '
                f'text-decoration: underline;">{mm.group(1)}</a>'
            ),
            line_with_imgs
        )
        out_lines.append(line_processed)

    flush_blockquote()
    md = '\n'.join(out_lines)

    md = re.sub(r'\*\*([^*\n]+)\*\*', lambda m: ph(f'<strong>{m.group(1)}</strong>'), md)
    md = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', lambda m: ph(f'<em>{m.group(1)}</em>'), md)
    md = md.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    md = re.sub(r'(https?://[^\s<>"]+)',
                rf'<a href="\1" style="color: {BRAND_LINK};">\1</a>', md)
    for key, val in placeholders.items():
        md = md.replace(key, val)

    def is_block(s):
        s = s.lstrip()
        return s.startswith(('<blockquote', '<hr', '<div', '<h1', '<h2', '<h3',
                             '<table', '<ul', '<ol', '<pre'))

    paragraphs = [p.strip() for p in md.split('\n\n') if p.strip()]
    out = []
    for p in paragraphs:
        if is_block(p):
            out.append(p)
        else:
            out.append(
                f'<p style="margin: 0 0 14px 0; line-height: 1.65; '
                f'color: #2a2a2a; font-size: 15px;">{p.replace(chr(10), "<br>")}</p>'
            )
    body_html = '\n'.join(out)

    return _wrap_html(body_html, footer_html)


def _send_via_ghl(contact_id, subject, html_body, plaintext_body, kind_label, log_extra=None):
    body = {
        "type": "Email",
        "contactId": contact_id,
        "subject": subject,
        "html": html_body,
        "message": plaintext_body or '',
    }
    log.info(f"  {kind_label} -> POST /conversations/messages")
    log.info(f"    Subject : {subject}")
    if log_extra:
        for k, v in log_extra.items():
            log.info(f"    {k}: {v}")
    resp = _ghl_post("/conversations/messages", body)
    conv_id = resp.get('conversationId')
    msg_id = resp.get('messageId') or resp.get('emailMessageId')
    log.info(f"  -> conversationId={conv_id} messageId={msg_id}")
    return resp, conv_id, msg_id


def action_send_email(conn, enr, step, ctx, rendered_subject, rendered_body):
    contact_id = ctx['contact'].get('id') or enr.get('ghl_contact_id')
    target_slug = step.get('action_target') or 'unknown'
    wf = (ctx or {}).get('workflow')
    # A footer nobody reads back is decoration. Marketing email checks the
    # opt-out list before it sends; transactional email never consults it,
    # because an unsubscribe is not a request to stop hearing about your own
    # booked session.
    if wf in MARKETING_WORKFLOWS and is_suppressed(conn, ctx):
        log.info(f"  send_email({target_slug}) SUPPRESSED - this contact has "
                 f"unsubscribed from marketing email")
        return {'external_ref': f"suppressed:{target_slug}",
                'payload': {'kind': 'suppressed_unsubscribed', 'target': target_slug,
                            'workflow': wf}}
    if not contact_id:
        raise ValueError("send_email: no GHL contact id on enrollment")
    if not rendered_subject:
        rendered_subject = f'(JHP - {target_slug})'
    html_body = _md_to_html(rendered_body, _legal_footer_html(ctx))
    resp, conv_id, msg_id = _send_via_ghl(
        contact_id, rendered_subject, html_body, rendered_body,
        kind_label=f"send_email({target_slug})",
    )
    return {
        'external_ref': f"ghl_email:{msg_id}" if msg_id else f"ghl_email:{target_slug}",
        'payload': {'kind': 'transactional_email', 'conversationId': conv_id,
                    'messageId': msg_id, 'subject': rendered_subject, 'target': target_slug},
    }


def action_send_sms(conn, enr, step, ctx, message):
    """Send an SMS to the contact via GHL Conversations. Respects the contact's
    SMS DND in GHL, and for MARKETING sequences also requires express consent,
    an opt-out that has not been used, and the quiet-hours window."""
    contact_id = ctx['contact'].get('id') or enr.get('ghl_contact_id')
    target_slug = step.get('action_target') or 'unknown'
    wf = (ctx or {}).get('workflow')
    if wf in MARKETING_WORKFLOWS:
        reason = sms_blocked_reason(ctx)
        if reason is None and is_suppressed(conn, ctx):
            reason = 'unsubscribed'
        if reason:
            log.info(f"  send_sms({target_slug}) NOT SENT - {reason}")
            return {'external_ref': f"sms_blocked:{target_slug}",
                    'payload': {'kind': 'sms_blocked', 'reason': reason,
                                'target': target_slug, 'workflow': wf}}
    if not contact_id:
        raise ValueError("send_sms: no GHL contact id on enrollment")
    if not message:
        raise ValueError("send_sms: empty message")
    body = {"type": "SMS", "contactId": contact_id, "message": message}
    log.info(f"  send_sms({target_slug}) -> POST /conversations/messages")
    resp = _ghl_post("/conversations/messages", body)
    conv_id = resp.get('conversationId')
    msg_id = resp.get('messageId') or resp.get('emailMessageId')
    log.info(f"  -> SMS conversationId={conv_id} messageId={msg_id}")
    return {
        'external_ref': f"ghl_sms:{msg_id}" if msg_id else f"ghl_sms:{target_slug}",
        'payload': {'kind': 'sms', 'conversationId': conv_id, 'messageId': msg_id, 'target': target_slug},
    }


def action_send_questionnaire(conn, enr, step, ctx, rendered_subject, rendered_body):
    cfg = step.get('action_config') or {}
    form_url = cfg.get('form_url')
    form_id = cfg.get('form_id')
    contact_id = ctx['contact'].get('id') or enr.get('ghl_contact_id')
    target_slug = step.get('action_target') or 'unknown'
    if not contact_id:
        raise ValueError("send_questionnaire: no GHL contact id on enrollment")
    if not form_url:
        log.warning(f"  send_questionnaire({target_slug}) - no form_url in action_config; "
                    f"recipient will see a placeholder link")
    if not rendered_subject:
        rendered_subject = f'(JHP questionnaire - {target_slug})'
    html_body = _md_to_html(rendered_body)
    resp, conv_id, msg_id = _send_via_ghl(
        contact_id, rendered_subject, html_body, rendered_body,
        kind_label=f"send_questionnaire({target_slug})",
        log_extra={'Form URL': form_url, 'Form ID': form_id},
    )
    return {
        'external_ref': f"ghl_questionnaire:{msg_id}" if msg_id else f"ghl_questionnaire:{target_slug}",
        'payload': {'kind': 'questionnaire_invite', 'conversationId': conv_id,
                    'messageId': msg_id, 'subject': rendered_subject,
                    'target': target_slug, 'form_url': form_url, 'form_id': form_id},
    }
