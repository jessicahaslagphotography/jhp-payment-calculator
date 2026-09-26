#!/usr/bin/env python3
"""
Workflow runner for JHP Boudoir (Jessica).

Ported/trimmed from R.H.L Boudoir (rhl-boudoir/workflow_runner.py).

Polls jhp_workflow_enrollments WHERE status='active' AND next_action_at <= NOW(),
executes the current step's action, advances the cursor, writes an audit row to
jhp_workflow_step_runs.

LIVE ACTIONS:
  send_email, send_questionnaire (hosted-form invite; action_config.email_note is
  appended to the invite, e.g. a coupon code), send_contract (hosted signing-page
  link), mark_milestone (label 'Pause...' pauses), todo, start_workflow.

GATING (Phase 3) — read from action_config, set by the gate migration:
  - reminder=true           -> SKIP this step if gate_form_slug (or any form)
                               has already been submitted (reminder-with-exit).
  - gate='contract_signed'  -> WAIT (re-poll) until gate_contract_slug (or any
                               contract) is signed.
  - gate='form_completed'   -> WAIT (re-poll) until gate_form_slug (or any form)
                               is submitted.
  - delay_relative_to in PROJECT_ANCHORS (before_/after_ project start/end) ->
                               fire relative to the contact's session date.

PSPP v2 form: the pick-and-pay checkout (page forms-pspp-setup-pspp-checkout-v2)
posts form_slug='pspp-setup-2026' into the psppv2_* pipeline. The form-completed
signal below checks form_responses + psppv2_form_inbox + psppv2_form_responses and
aliases that slug to PSPP_SETUP_SLUG, so the gate fires regardless of pipeline.

SESSION DATE source: enrollment.context.session_date (ISO string). Until present,
session-anchored steps re-poll (never fire) — safe.

NOT yet gated: 'invoice is paid in full' steps fire on their delay (no payment
signal wired). These flows are normally entered post-payment.

MERGE FIELDS: render_text() substitutes Dubsado tokens we know and blanks the
rest, so unmapped tokens never crash a send.
"""
import os
import sys
import re
import json
import logging
import secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
import psycopg2
import psycopg2.extras

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import email_actions  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('workflow_runner')

UTC = timezone.utc
MAX_ENROLLMENTS_PER_RUN = 100
WAIT_REPOLL_MINUTES = 10
PROJECT_WAIT_REPOLL_MINUTES = 360

PROJECT_ANCHORS = {
    'project_start', 'project_end',
    'before_project_start', 'after_project_start',
    'before_project_end', 'after_project_end',
}

SIGNATURE = os.environ.get('JHP_EMAIL_SIGNATURE', 'With love,\nJessica\nJHP Boudoir')
SIGN_BASE = os.environ.get('JHP_SIGN_BASE', 'https://pages.scalogy.com/jhpboudoir1/sign-contract/')
PSPP_SETUP_SLUG = 'pre-session-payment-plan-setup-form-lpl'
CONFIRM_BASE = os.environ.get('JHP_CONFIRM_BASE',
                              'https://pages.scalogy.com/jhpboudoir1/confirm-session/')
CONFIRM_BUTTON_BG = '#9a7b4f'


def now_utc():
    return datetime.now(UTC)


def connect():
    return psycopg2.connect(
        dbname=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        host=os.environ['PGHOST'],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def slugify(s):
    return re.sub(r'[^a-z0-9]+', '-', (s or '').lower()).strip('-')


def with_prefill(url, c):
    if not url:
        return url
    parts = []
    if c.get('id'):
        parts.append('ghl_id=' + quote(str(c['id'])))
    if c.get('name'):
        parts.append('name=' + quote(c['name']))
    if c.get('email'):
        parts.append('email=' + quote(c['email']))
    if not parts:
        return url
    return url + ('&' if '?' in url else '?') + '&'.join(parts)


def parse_dt(v):
    try:
        d = datetime.fromisoformat(str(v).replace('Z', '+00:00'))
        return d if d.tzinfo else d.replace(tzinfo=UTC)
    except Exception:
        return None


# ----------------------------------------------------------------------------
# Session confirmation (the "Confirm My Session" button in the countdown emails)
# ----------------------------------------------------------------------------

def ensure_confirm_token(conn, enr, ctx):
    """Return this enrollment's confirm token, minting the session_confirmations
    row on first use.

    Minted lazily rather than at enrollment time so the 16 journeys already in
    flight when this shipped pick a token up on their next countdown email,
    with no backfill. Keyed on enrollment_id (unique index), so a concurrent
    runner can't create a second token for the same journey.

    Returns None if anything goes wrong — the caller then renders the email
    without a button rather than with a dead one.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT token, status FROM session_confirmations "
                        "WHERE enrollment_id=%s", (enr['id'],))
            row = cur.fetchone()
            if row:
                return row['token'], row['status']

        c = ctx.get('contact') or {}
        sd = ctx.get('session_date')
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO session_confirmations "
                "(token, enrollment_id, workflow_id, ghl_contact_id, contact_name, "
                " contact_email, session_datetime) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s) "
                # The unique index is partial (WHERE enrollment_id IS NOT NULL),
                # so the conflict target has to repeat that predicate to match it.
                "ON CONFLICT (enrollment_id) WHERE enrollment_id IS NOT NULL DO UPDATE SET "
                "  session_datetime = EXCLUDED.session_datetime, updated_at = NOW() "
                "RETURNING token, status",
                (secrets.token_urlsafe(24), enr['id'], enr['workflow_id'],
                 c.get('id'), c.get('name'), c.get('email'), sd))
            new = cur.fetchone()
            return new['token'], new['status']
    except Exception as e:
        log.warning(f"  confirm token unavailable for enrollment {enr['id']}: {e}")
        return None, None


def build_confirm_assets(conn, enr, ctx):
    """Build the {{confirm_url}} / {{confirm_button}} / {{confirm_sms}} merge values.

    A client confirms ONCE. Every countdown email after that still goes out —
    they carry the directions and the timeline, which she needs — but the ask is
    replaced by a short 'you're confirmed, nothing to do' notice. Being asked to
    confirm four more times after you already did reads like your confirmation
    never registered.

    The URL carries the token plus a display-only first name and session label,
    so the page can greet the client without reading the database (page-api
    tokens live 15 minutes; these links get opened weeks later).

    Returns ('', '', '') when no token could be minted, which blanks the ask out
    of the email entirely — an email with no button beats one with a dead link.
    """
    token, status = ensure_confirm_token(conn, enr, ctx)
    if not token:
        return '', '', ''

    if status == 'confirmed':
        # Already confirmed: reassure, don't re-ask. No URL is exposed, so an
        # SMS built from {{confirm_url}} cannot trail off into a bare colon.
        notice = (
            f'<div style="text-align:center;margin:28px 0">'
            f'<div style="display:inline-block;border:1px solid #d7e7de;'
            f'background:#f1f7f3;color:#3f7d58;padding:12px 28px;border-radius:2px;'
            f'font-size:13px;letter-spacing:1.2px;text-transform:uppercase;'
            f'font-weight:600">&#10003; You&rsquo;re confirmed</div>'
            f'<div style="margin-top:10px;font-size:13px;color:#6b6259">'
            f'Thanks for confirming &mdash; nothing else to do. '
            f'This is just your reminder.</div></div>'
        )
        return '', notice, "You're already confirmed, so this is just your reminder."

    c = ctx.get('contact') or {}
    parts = ['t=' + quote(token)]
    if c.get('first_name'):
        parts.append('n=' + quote(c['first_name']))
    sd = ctx.get('session_date')
    if sd:
        try:
            parts.append('d=' + quote(sd.strftime('%A, %B %-d at %-I:%M %p')))
        except Exception:
            pass
    url = CONFIRM_BASE + ('&' if '?' in CONFIRM_BASE else '?') + '&'.join(parts)

    button = (
        f'<div style="text-align:center;margin:28px 0">'
        f'<a href="{url}" style="display:inline-block;background:{CONFIRM_BUTTON_BG};'
        f'color:#ffffff;padding:14px 36px;text-decoration:none;border-radius:2px;'
        f'font-size:13px;letter-spacing:1.2px;text-transform:uppercase;font-weight:500">'
        f'Confirm My Session</a>'
        f'<div style="margin-top:10px;font-size:13px;color:#6b6259">'
        f'One tap lets us know to expect you.</div></div>'
    )

    # A whole line, not a bare URL: an SMS needs the label and the link to appear
    # or vanish together once she has confirmed.
    sms_line = "CONFIRM YOU'LL BE THERE:\n" + CONFIRM_BASE + (
        '&' if '?' in CONFIRM_BASE else '?') + 't=' + quote(token)
    return url, button, sms_line


# ----------------------------------------------------------------------------
# skip_if expression evaluator
# ----------------------------------------------------------------------------

def resolve_path(ctx, path):
    cur = ctx
    for p in path.split('.'):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(p)
        elif isinstance(cur, list):
            try:
                cur = cur[int(p)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return cur


def evaluate(expr, ctx):
    if expr is None:
        return None
    if not isinstance(expr, dict):
        return expr
    if 'path' in expr:
        return resolve_path(ctx, expr['path'])
    if 'literal' in expr:
        return expr['literal']
    op = expr.get('op')
    a = expr.get('args', [])
    if op == 'eq':  return evaluate(a[0], ctx) == evaluate(a[1], ctx)
    if op == 'neq': return evaluate(a[0], ctx) != evaluate(a[1], ctx)
    if op == 'gt':  return evaluate(a[0], ctx) > evaluate(a[1], ctx)
    if op == 'lt':  return evaluate(a[0], ctx) < evaluate(a[1], ctx)
    if op == 'gte': return evaluate(a[0], ctx) >= evaluate(a[1], ctx)
    if op == 'lte': return evaluate(a[0], ctx) <= evaluate(a[1], ctx)
    if op == 'and': return all(bool(evaluate(x, ctx)) for x in a)
    if op == 'or':  return any(bool(evaluate(x, ctx)) for x in a)
    if op == 'not': return not bool(evaluate(a[0], ctx))
    if op == 'exists':
        v = evaluate(a[0], ctx)
        if v is None: return False
        if isinstance(v, (list, dict, str)) and len(v) == 0: return False
        return True
    raise ValueError(f"Unknown op: {op}")


# ----------------------------------------------------------------------------
# Context + merge-field rendering
# ----------------------------------------------------------------------------

def build_context(conn, enr):
    # The workflow's own name, so email_actions can tell a marketing send from a
    # transactional one. Added 2026-09-26 with the CAN-SPAM footer: only
    # marketing email may carry an unsubscribe link, because GHL's email DND is
    # account-wide and a client who used it would stop receiving her own session
    # confirmations too.
    wf_name = None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM jhp_workflows WHERE id=%s", (enr['workflow_id'],))
            r = cur.fetchone()
            wf_name = (r or {}).get('name')
    except Exception as e:
        log.warning(f"  could not read the workflow name: {e}")

    name = (enr.get('contact_name') or '').strip()
    email = (enr.get('contact_email') or '').strip()
    ghl_id = enr.get('ghl_contact_id')
    phone = None
    if email:
        with conn.cursor() as cur:
            cur.execute("SELECT ghl_id, name, phone FROM ghl_contacts WHERE lower(email)=lower(%s) LIMIT 1", (email,))
            r = cur.fetchone()
            if r:
                ghl_id = ghl_id or r['ghl_id']
                name = name or (r['name'] or '')
                phone = r['phone']
    first_name = name.split()[0] if name else 'there'

    signed = set()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT form_slug FROM form_responses WHERE form_slug LIKE 'contract:%%' "
            "AND COALESCE(signature,'') <> '' "
            "AND ((%s <> '' AND ghl_contact_id = %s) OR (%s <> '' AND lower(contact_email)=lower(%s)))",
            (ghl_id or '', ghl_id or '', email, email))
        for r in cur.fetchall():
            s = r['form_slug'] or ''
            if s.startswith('contract:'):
                signed.add(s.split(':', 1)[1])

    # Form-completed signal. Generic forms land in form_responses (form:<slug>).
    # The PSPP v2 pick-and-pay form posts 'pspp-setup-2026' into the psppv2_*
    # pipeline, so check those tables too and alias to PSPP_SETUP_SLUG.
    submitted = set()
    _cond = "((%s <> '' AND ghl_contact_id = %s) OR (%s <> '' AND lower(contact_email)=lower(%s)))"
    _p = (ghl_id or '', ghl_id or '', email, email)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT form_slug FROM form_responses "
            "WHERE (form_slug LIKE 'form:%%' OR form_slug LIKE 'pspp-setup-2026%%') AND " + _cond +
            " UNION ALL SELECT form_slug FROM psppv2_form_inbox "
            "WHERE form_slug LIKE 'pspp-setup-2026%%' AND is_test IS NOT TRUE AND process_status='processed' AND " + _cond +
            " UNION ALL SELECT form_slug FROM psppv2_form_responses "
            "WHERE form_slug LIKE 'pspp-setup-2026%%' AND is_test IS NOT TRUE AND square_status LIKE 'completed%%' AND " + _cond,
            _p + _p + _p)
        for r in cur.fetchall():
            s = r['form_slug'] or ''
            if s.startswith('form:'):
                submitted.add(s.split(':', 1)[1])
            elif s.startswith('pspp-setup-2026'):
                submitted.add(PSPP_SETUP_SLUG)

    ectx = enr.get('context') or {}
    session_date = parse_dt(ectx.get('session_date')) if isinstance(ectx, dict) else None

    return {
        'workflow': wf_name,
        'contact': {'id': ghl_id, 'name': name, 'first_name': first_name,
                    'email': email, 'phone': phone or ''},
        'enrollment': {'id': enr['id'], 'context': ectx},
        'signed_contract_slugs': sorted(signed),
        'contract_signed': len(signed) > 0,
        'submitted_form_slugs': sorted(submitted),
        'form_submitted': len(submitted) > 0,
        'session_date': session_date,
        'now': now_utc(),
    }


def render_text(text, ctx, cfg):
    if not text:
        return ''
    c = ctx.get('contact') or {}
    form_url = (cfg or {}).get('form_url') or ''
    enr_ctx = (ctx.get('enrollment') or {}).get('context') or {}
    if not isinstance(enr_ctx, dict):
        enr_ctx = {}
    sd = ctx.get('session_date')
    session_str = ''
    if sd:
        try:
            session_str = sd.strftime('%B %-d, %Y %-I:%M %p')
        except Exception:
            session_str = sd.isoformat()
    values = {
        'client.firstname': c.get('first_name', ''),
        'client.first_name': c.get('first_name', ''),
        'contact.first_name': c.get('first_name', ''),
        'first_name': c.get('first_name', ''),
        'client.name': c.get('name', ''),
        'client.fullname': c.get('name', ''),
        'contact.name': c.get('name', ''),
        'name': c.get('name', ''),
        'client.email': c.get('email', ''),
        'contact.email': c.get('email', ''),
        'brand.emailtemplate.signature': SIGNATURE,
        'form.url': form_url,
        'form_url': form_url,
        'appointment.start_time': session_str,
        'session_date': session_str,
        'booking_deadline': enr_ctx.get('booking_deadline', ''),
        'book_url': enr_ctx.get('book_url', ''),
        'booking_url': enr_ctx.get('book_url', ''),
        'deadline': enr_ctx.get('booking_deadline', ''),
        'promo_code': enr_ctx.get('promo_code', ''),
        # Additive (2026-09-25, for website_inquiry_2027). Both come off the
        # enrollment context and both default to '' exactly as an unmapped
        # token already did, so no existing step body changes behaviour.
        'guide_url': enr_ctx.get('guide_url', ''),
        'calendar_url': enr_ctx.get('calendar_url', ''),
        # Set by process_enrollment for steps whose body carries the button.
        # Blank everywhere else, which is exactly the no-button behaviour.
        'confirm_url': ctx.get('confirm_url', '') or '',
        'confirm_button': ctx.get('confirm_button', '') or '',
        'confirm_sms': ctx.get('confirm_sms', '') or '',
    }

    def repl(m):
        token = m.group(1).strip()
        key = token.split('|')[0].strip().lower()
        return values.get(key, '')

    return re.sub(r'\{\{\s*(.+?)\s*\}\}', repl, text)


def _render_subject_and_body(step, ctx):
    cfg = step.get('action_config') or {}
    target = step.get('action_target') or 'unknown'
    subject = cfg.get('subject') or f'[{target}]'
    body_md = cfg.get('body_md') or ''
    try:
        return render_text(subject, ctx, cfg), (render_text(body_md, ctx, cfg) if body_md else '')
    except Exception as e:
        log.warning(f"  merge-field render failed for {target}: {e}")
        return subject, body_md


# ----------------------------------------------------------------------------
# Step navigation
# ----------------------------------------------------------------------------

def get_step_at_position(conn, workflow_id, position):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM jhp_workflow_steps WHERE workflow_id=%s AND position=%s",
                    (workflow_id, position))
        return cur.fetchone()


def get_next_step(conn, workflow_id, current_position):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM jhp_workflow_steps WHERE workflow_id=%s AND position>%s "
                    "ORDER BY position ASC LIMIT 1", (workflow_id, current_position))
        return cur.fetchone()


def add_delay(start, amount, unit):
    if not amount:
        return start
    if unit == 'minutes': return start + timedelta(minutes=amount)
    if unit == 'hours':   return start + timedelta(hours=amount)
    if unit == 'days':    return start + timedelta(days=amount)
    if unit == 'weeks':   return start + timedelta(weeks=amount)
    return start + timedelta(minutes=amount)


def compute_fire_time(enr, step):
    rel = step.get('delay_relative_to') or 'previous_step'
    amount = step.get('delay_amount') or 0
    unit = step.get('delay_unit') or 'minutes'
    if rel in PROJECT_ANCHORS:
        return now_utc()  # gated/scheduled in process_enrollment
    base = enr['enrolled_at'] if rel == 'enrollment' else now_utc()
    fire_at = add_delay(base, amount, unit)
    return fire_at if fire_at >= now_utc() else now_utc()


def set_cursor(conn, enr, next_step):
    fire_at = compute_fire_time(enr, next_step)
    with conn.cursor() as cur:
        cur.execute("UPDATE jhp_workflow_enrollments SET current_step_position=%s, "
                    "next_action_at=%s, updated_at=NOW() WHERE id=%s",
                    (next_step['position'], fire_at, enr['id']))
    log.info(f"  -> cursor to step {next_step['position']}, fires {fire_at.isoformat()}")


def advance_to_next(conn, enr, current_step):
    nxt = get_next_step(conn, enr['workflow_id'], current_step['position'])
    if not nxt:
        complete_enrollment(conn, enr['id'])
        return
    set_cursor(conn, enr, nxt)


def complete_enrollment(conn, enr_id):
    with conn.cursor() as cur:
        cur.execute("UPDATE jhp_workflow_enrollments SET status='completed', completed_at=NOW(), "
                    "next_action_at=NULL, updated_at=NOW() WHERE id=%s", (enr_id,))
    log.info(f"  -> enrollment {enr_id} completed")


def mark_errored(conn, enr_id, msg):
    with conn.cursor() as cur:
        cur.execute("UPDATE jhp_workflow_enrollments SET status='errored', cancelled_reason=%s, "
                    "next_action_at=NULL, updated_at=NOW() WHERE id=%s", (msg[:500], enr_id))
    log.error(f"  -> enrollment {enr_id} errored: {msg}")


def reschedule_wait(conn, enr_id, minutes=WAIT_REPOLL_MINUTES):
    with conn.cursor() as cur:
        cur.execute("UPDATE jhp_workflow_enrollments SET next_action_at=NOW()+(%s||' minutes')::interval, "
                    "updated_at=NOW() WHERE id=%s", (str(minutes), enr_id))


def reschedule_at(conn, enr_id, when):
    with conn.cursor() as cur:
        cur.execute("UPDATE jhp_workflow_enrollments SET next_action_at=%s, updated_at=NOW() WHERE id=%s",
                    (when, enr_id))


def record_run(conn, enr_id, step, status, **kw):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO jhp_workflow_step_runs (enrollment_id, step_id, step_position, status, "
            "completed_at, skip_if_result, external_ref, error_message, payload) "
            "VALUES (%s,%s,%s,%s,NOW(),%s,%s,%s,%s::jsonb)",
            (enr_id, step['id'], step['position'], status, kw.get('skip_if_result'),
             kw.get('external_ref'), kw.get('error_message'),
             json.dumps(kw.get('payload', {}), default=str)))


# ----------------------------------------------------------------------------
# Actions
# ----------------------------------------------------------------------------

def execute_action(conn, enr, step, ctx):
    kind = step.get('action_kind')
    target = step.get('action_target')
    c = ctx.get('contact') or {}
    first = c.get('first_name') or 'there'

    if kind == 'send_email':
        subj, body = _render_subject_and_body(step, ctx)
        return email_actions.action_send_email(conn, enr, step, ctx, subj, body)

    if kind == 'send_email_sms':
        cfg = step.get('action_config') or {}
        subj, body = _render_subject_and_body(step, ctx)
        res = email_actions.action_send_email(conn, enr, step, ctx, subj, body)
        sms_text = render_text(cfg.get('sms') or '', ctx, cfg)
        if sms_text:
            try:
                sres = email_actions.action_send_sms(conn, enr, step, ctx, sms_text)
                res.setdefault('payload', {})['sms'] = sres.get('payload')
            except Exception as e:
                log.warning(f"  sms send failed (email delivered ok): {e}")
        return res

    if kind == 'send_sms':
        cfg = step.get('action_config') or {}
        sms_text = render_text(cfg.get('sms') or cfg.get('body_md') or '', ctx, cfg)
        return email_actions.action_send_sms(conn, enr, step, ctx, sms_text)

    if kind == 'send_questionnaire':
        cfg = step.get('action_config') or {}
        form_url = with_prefill(cfg.get('form_url') or '', c)
        subject = render_text(cfg.get('subject') or f'Please complete: {target}', ctx, cfg)
        note = cfg.get('email_note')
        note_block = ('\n\n' + render_text(note, ctx, cfg)) if note else ''
        if form_url:
            body = (f"Hi {first}!\n\nWhen you have a moment, please complete **{target}**:\n\n"
                    f"[Open the form]({form_url})" + note_block + f"\n\nThank you!\n\n{SIGNATURE}")
        else:
            body = (f"Hi {first}!\n\nPlease complete **{target}**" + note_block +
                    f"\n\nThank you!\n\n{SIGNATURE}")
        res = email_actions.action_send_questionnaire(conn, enr, step, ctx, subject, body)
        res.setdefault('payload', {})['form_url'] = form_url
        return res

    if kind == 'send_contract':
        slug = slugify(target)
        url = SIGN_BASE + ('&' if '?' in SIGN_BASE else '?') + 'c=' + quote(slug)
        sign_url = with_prefill(url, c)
        cfg = step.get('action_config') or {}
        full = cfg.get('body_md') or ''
        cover = full.split('— — — CONTRACT DOCUMENT')[0].strip() if full else ''
        cover = render_text(cover, ctx, cfg)
        subject = render_text(cfg.get('subject') or f'Please review & sign: {target}', ctx, cfg)
        body = (cover + "\n\n" if cover else '') + "[Review & Sign Your Contract](" + sign_url + ")"
        res = email_actions.action_send_email(conn, enr, step, ctx, subject, body)
        res.setdefault('payload', {})['sign_url'] = sign_url
        res.setdefault('payload', {})['contract_slug'] = slug
        return res

    if kind == 'todo':
        log.info(f"  todo: {target}")
        return {'external_ref': f"todo:{step['id']}", 'payload': {'note': target}}

    if kind == 'mark_milestone':
        label = (step.get('label') or target or '').strip()
        if label.lower().startswith('pause'):
            with conn.cursor() as cur:
                cur.execute("UPDATE jhp_workflow_enrollments SET status='paused', "
                            "next_action_at=NULL, updated_at=NOW() WHERE id=%s", (enr['id'],))
            log.info(f"  pause via milestone -> enrollment {enr['id']} paused")
            return {'external_ref': f"pause:enr{enr['id']}", 'payload': {'paused': True, 'label': label}}
        log.info(f"  mark_milestone: {label}")
        return {'external_ref': f"milestone:{step['id']}", 'payload': {'label': label}}

    if kind == 'start_workflow':
        cfg = step.get('action_config') or {}
        tname = cfg.get('target_workflow') or target
        if not tname:
            raise ValueError("start_workflow: no target")
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jhp_workflows WHERE dubsado_name=%s OR display_name=%s OR name=%s "
                        "ORDER BY id LIMIT 1", (tname, tname, tname))
            wf = cur.fetchone()
        if not wf:
            raise ValueError(f"start_workflow: target '{tname}' not found")
        twid = wf['id']
        with conn.cursor() as cur:
            cur.execute("SELECT MIN(position) AS p FROM jhp_workflow_steps WHERE workflow_id=%s", (twid,))
            mn = cur.fetchone()
        first_pos = mn['p'] if mn and mn['p'] is not None else 1
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jhp_workflow_enrollments WHERE workflow_id=%s AND ghl_contact_id "
                        "IS NOT DISTINCT FROM %s AND status IN ('active','paused') LIMIT 1",
                        (twid, enr.get('ghl_contact_id')))
            existing = cur.fetchone()
        if existing:
            log.info(f"  start_workflow({tname}) -> already enrolled #{existing['id']}")
            return {'external_ref': f"start_workflow:{tname}:already:{existing['id']}"}
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO jhp_workflow_enrollments (workflow_id, contact_id, ghl_contact_id, "
                "contact_name, contact_email, status, current_step_position, next_action_at, "
                "context, enrolled_by) VALUES (%s,%s,%s,%s,%s,'active',%s,NOW(),%s::jsonb,%s) RETURNING id",
                (twid, enr.get('contact_id'), enr.get('ghl_contact_id'), enr.get('contact_name'),
                 enr.get('contact_email'), first_pos, json.dumps(enr.get('context') or {}),
                 f"workflow_runner:enr{enr['id']}"))
            new = cur.fetchone()
        log.info(f"  start_workflow({tname}) -> enrolled #{new['id']}")
        return {'external_ref': f"start_workflow:{tname}:enrolled:{new['id']}"}

    raise ValueError(f"Unknown action_kind: {kind}")


# ----------------------------------------------------------------------------
# Enrollment processor
# ----------------------------------------------------------------------------

def process_enrollment(conn, enr):
    log.info(f"Enrollment #{enr['id']} (wf {enr['workflow_id']}, pos {enr['current_step_position']})")
    pos = enr['current_step_position'] or 0
    step = get_step_at_position(conn, enr['workflow_id'], pos)
    if not step:
        step = get_next_step(conn, enr['workflow_id'], pos)
        if not step:
            log.info(f"  no step at/after {pos} - completing")
            complete_enrollment(conn, enr['id'])
            return
    spos = step['position']
    log.info(f"  step {spos} ({step.get('label') or step.get('action_target')}) kind={step.get('action_kind')}")
    ctx = build_context(conn, enr)
    cfg = step.get('action_config') or {}

    # Mint the confirm token only for steps that actually render it, so we don't
    # create a session_confirmations row for every journey in the tenant. The SMS
    # body counts too - an SMS-only step must not ship with a blank link.
    _confirm_src = (cfg.get('body_md') or '') + (cfg.get('sms') or '')
    if 'confirm_button' in _confirm_src or 'confirm_url' in _confirm_src \
            or 'confirm_sms' in _confirm_src:
        (ctx['confirm_url'], ctx['confirm_button'],
         ctx['confirm_sms']) = build_confirm_assets(conn, enr, ctx)

    # skip_if (structured AST)
    if step.get('skip_if'):
        try:
            if bool(evaluate(step['skip_if'], ctx)):
                log.info("  -> skipped (skip_if)")
                record_run(conn, enr['id'], step, 'skipped', skip_if_result=True)
                advance_to_next(conn, enr, step)
                return
        except Exception as e:
            log.warning(f"  skip_if eval failed: {e}")

    # Reminder-with-exit: skip if the gating form is already submitted.
    if cfg.get('reminder'):
        fslug = cfg.get('gate_form_slug')
        done = (fslug in ctx['submitted_form_slugs']) if fslug else ctx['form_submitted']
        if done:
            log.info(f"  step {spos} reminder skipped — form already completed ({fslug or 'any'})")
            record_run(conn, enr['id'], step, 'skipped', payload={'reason': 'form_completed'})
            advance_to_next(conn, enr, step)
            return

    # Gate: wait until a contract is signed.
    gate = cfg.get('gate')
    if gate == 'contract_signed':
        cslug = cfg.get('gate_contract_slug')
        ok = (cslug in ctx['signed_contract_slugs']) if cslug else ctx['contract_signed']
        if not ok:
            log.info(f"  step {spos} waiting for contract signed ({cslug or 'any'}) — re-poll {WAIT_REPOLL_MINUTES}m")
            reschedule_wait(conn, enr['id'])
            return

    # Gate: wait until a form is completed.
    if gate == 'form_completed':
        fslug = cfg.get('gate_form_slug')
        ok = (fslug in ctx['submitted_form_slugs']) if fslug else ctx['form_submitted']
        if not ok:
            log.info(f"  step {spos} waiting for form completed ({fslug or 'any'}) — re-poll {WAIT_REPOLL_MINUTES}m")
            reschedule_wait(conn, enr['id'])
            return

    # Session-date anchored timing.
    rel = step.get('delay_relative_to') or ''
    if rel in PROJECT_ANCHORS:
        sd = ctx.get('session_date')
        if sd is None:
            log.info(f"  step {spos} session-anchored, no session date — re-poll in {PROJECT_WAIT_REPOLL_MINUTES}m")
            reschedule_wait(conn, enr['id'], minutes=PROJECT_WAIT_REPOLL_MINUTES)
            return
        amount = step.get('delay_amount') or 0
        unit = step.get('delay_unit') or 'days'
        signed_amt = -amount if rel.startswith('before_') else amount
        target = add_delay(sd, signed_amt, unit)
        if now_utc() < target:
            reschedule_at(conn, enr['id'], target)
            log.info(f"  step {spos} not due until {target.isoformat()} (session {sd.isoformat()}) — rescheduled")
            return
        # Past-due session-anchored step. If flagged skip_if_past and the intended
        # window closed more than a day ago (near-booking case), skip rather than
        # fire — keeps numbered countdown emails from sending with a wrong number.
        if cfg.get('skip_if_past') and (now_utc() - target) > timedelta(days=1):
            log.info(f"  step {spos} skip_if_past — window closed {target.isoformat()} — skipping")
            record_run(conn, enr['id'], step, 'skipped', payload={'reason': 'window_passed', 'target': target.isoformat()})
            advance_to_next(conn, enr, step)
            return

    try:
        result = execute_action(conn, enr, step, ctx)
        record_run(conn, enr['id'], step, 'completed', **result)
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM jhp_workflow_enrollments WHERE id=%s", (enr['id'],))
            cur_status = (cur.fetchone() or {}).get('status')
        if cur_status == 'active':
            advance_to_next(conn, enr, step)
    except Exception as e:
        log.error(f"  action failed: {e}")
        record_run(conn, enr['id'], step, 'failed', error_message=str(e))
        mark_errored(conn, enr['id'], f"step {spos}: {e}")


def main():
    log.info("JHP workflow runner starting")
    conn = connect()
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # next_action_at IS NULL => a freshly hand-assigned enrollment (no start
            # time set); treat it as due now so manual assignment fires immediately.
            cur.execute("SELECT * FROM jhp_workflow_enrollments WHERE status='active' "
                        "AND (next_action_at IS NULL OR next_action_at <= NOW()) "
                        "ORDER BY next_action_at ASC NULLS FIRST LIMIT %s "
                        "FOR UPDATE SKIP LOCKED", (MAX_ENROLLMENTS_PER_RUN,))
            due = cur.fetchall()
        log.info(f"{len(due)} due enrollment(s)")
        for enr in due:
            try:
                process_enrollment(conn, enr)
                conn.commit()
            except Exception as e:
                conn.rollback()
                log.exception(f"enrollment {enr['id']} crashed")
                try:
                    mark_errored(conn, enr['id'], f"runner crash: {e}")
                    conn.commit()
                except Exception:
                    conn.rollback()
        log.info("JHP workflow runner finished")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
