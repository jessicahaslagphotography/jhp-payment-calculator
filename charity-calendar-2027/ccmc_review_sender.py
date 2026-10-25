#!/usr/bin/env python3
"""ccmc-review-sender: turn Jessica's review decisions into sends.

Cron, every 5 minutes. Jessica reviews 2027 Charity Calendar Model Call
applications on the private review page, which only flips
charity_calendar_applications.status. Everything that leaves the building
happens here, so nothing a visitor can reach can send anything:

  approved  -> mint invite_token + 72h claim_deadline, status 'invited',
               enroll the contact in jhp_workflows 'ccmc_invite' (day 0 / 1 / 2
               email + text, sent by jhp-workflow-runner)
  backup    -> (not selected) mint invite_token + 72h claim_deadline, status
               'backup_sent', enroll in 'ccmc_saveahead' (not-selected email + text
               with the SAME $99 / $500-off offer and her personal claim link,
               day 0 / 1 / 2). Unclaimed after 72h -> 'released' quietly.
  invited, deadline passed, not claimed
            -> status 'released', cancel the invite enrollment, alert Jessica
               so she can personally approve the next woman in line
  claimed/booked/forfeited/released/declined
            -> cancel any still-active ccmc_invite enrollment
  new (unseen) -> one owner alert per application with a link to the review page

The claim page and its charger (ccmc-reserve-charge) set status 'claimed';
this script only reads that.

KILL SWITCH: pause this workflow. Already-enrolled sends are stopped by
setting their jhp_workflow_enrollments rows to 'cancelled'.
"""
import os
import json
import secrets
import datetime
import psycopg2
import psycopg2.extras

JESSICA_EMAIL = "jessicahaslagphotography@gmail.com"
CLAIM_BASE = "https://pages.scalogy.com/jhpboudoir1/ccmc-claim/?t="
REVIEW_URL = "https://pages.scalogy.com/jhpboudoir1/ccmc-review-cl4f7nwt/"
CONSULT_URL = "https://api.leadconnectorhq.com/widget/booking/mi2EqYRq4gGEbBJHe82b"
CLAIM_HOURS = 72
CENTRAL = datetime.timezone(datetime.timedelta(hours=-5))  # CDT, matches the page window

INVITE_WF = "ccmc_invite"
SAVEAHEAD_WF = "ccmc_saveahead"
TERMINAL = ("claimed", "booked", "forfeited", "released", "declined", "paid")

PKG = {"combo": "Combo collection", "digital": "Digital collection",
       "experience-only": "Experience only"}
PAY = {"pay-in-full": "Pay in full", "prepayment-plan": "Prepayment plan",
       "cannot-afford": "Can't afford a package"}


def now():
    return datetime.datetime.now(datetime.timezone.utc)


def fmt_deadline(dt):
    local = dt.astimezone(CENTRAL)
    return local.strftime("%A, %B %-d at %-I:%M %p")


def connect():
    conn = psycopg2.connect(dbname=os.environ["PGDATABASE"], user=os.environ["PGUSER"],
                            host=os.environ["PGHOST"],
                            cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = True
    return conn


def workflow_id(cur, name):
    cur.execute("SELECT id FROM jhp_workflows WHERE name=%s", (name,))
    r = cur.fetchone()
    if not r:
        raise SystemExit(f"jhp_workflows row {name!r} is missing")
    return r["id"]


def owner_alert(cur, subject, message):
    cur.execute(
        "INSERT INTO action_queue (action, email, subject, message, status, created_at) "
        "VALUES (%s,%s,%s,%s,'pending', NOW())",
        ("owner_ccmc_alert", JESSICA_EMAIL, subject, message))


def enroll(cur, wid, app, ctx):
    cur.execute(
        "INSERT INTO jhp_workflow_enrollments "
        "(workflow_id, ghl_contact_id, contact_name, contact_email, status, "
        " current_step_position, next_action_at, context, enrolled_by) "
        "VALUES (%s,%s,%s,%s,'active',1,NOW(),%s::jsonb,'ccmc_review_sender') RETURNING id",
        (wid, app["ghl_contact_id"], app["contact_name"], app["contact_email"], json.dumps(ctx)))
    return cur.fetchone()["id"]


def cancel_enrollment(cur, enr_id, reason):
    if not enr_id:
        return 0
    cur.execute(
        "UPDATE jhp_workflow_enrollments SET status='cancelled', cancelled_reason=%s, updated_at=NOW() "
        "WHERE id=%s AND status IN ('active','paused')", (reason, enr_id))
    return cur.rowcount


def main():
    conn = connect()
    cur = conn.cursor()
    invite_wid = workflow_id(cur, INVITE_WF)
    save_wid = workflow_id(cur, SAVEAHEAD_WF)

    # 1. Approved -> invite.
    cur.execute("SELECT * FROM charity_calendar_applications WHERE status='approved' ORDER BY decided_at NULLS LAST, id")
    for app in cur.fetchall():
        if not app["contact_email"]:
            print(f"app {app['id']}: no email, cannot invite")
            continue
        token = app["invite_token"] or secrets.token_hex(16)
        deadline = now() + datetime.timedelta(hours=CLAIM_HOURS)
        ctx = {"book_url": CLAIM_BASE + token, "booking_deadline": fmt_deadline(deadline),
               "ccmc_application_id": app["id"]}
        enr_id = enroll(cur, invite_wid, app, ctx)
        cur.execute(
            "UPDATE charity_calendar_applications SET status='invited', invite_token=%s, "
            "invited_at=NOW(), claim_deadline=%s, enrollment_id=%s, processed_status='invited' "
            "WHERE id=%s AND status='approved'", (token, deadline, enr_id, app["id"]))
        print(f"app {app['id']}: invited, deadline {deadline.isoformat()}, enrollment {enr_id}")

    # 2. Backup (not selected) -> Save-Ahead offer with her own 72h claim link.
    #    Same $99 (or $1 hold) / $500-off offer as an invite (Jessica 2026-10-25).
    cur.execute("SELECT * FROM charity_calendar_applications WHERE status='backup' ORDER BY id")
    for app in cur.fetchall():
        if not app["contact_email"]:
            print(f"app {app['id']}: no email, cannot send the save-ahead offer")
            continue
        token = app["invite_token"] or secrets.token_hex(16)
        deadline = now() + datetime.timedelta(hours=CLAIM_HOURS)
        ctx = {"book_url": CLAIM_BASE + token, "booking_deadline": fmt_deadline(deadline),
               "ccmc_application_id": app["id"]}
        enr_id = enroll(cur, save_wid, app, ctx)
        cur.execute(
            "UPDATE charity_calendar_applications SET status='backup_sent', invite_token=%s, "
            "invited_at=NOW(), claim_deadline=%s, enrollment_id=%s, processed_status='backup_sent' "
            "WHERE id=%s AND status='backup'", (token, deadline, enr_id, app["id"]))
        print(f"app {app['id']}: save-ahead offer enrolled {enr_id}, deadline {deadline.isoformat()}")

    # 3. Expired invitations -> release + alert.
    cur.execute(
        "SELECT * FROM charity_calendar_applications WHERE status IN ('invited','backup_sent') "
        "AND claim_deadline IS NOT NULL AND claim_deadline < NOW()")
    for app in cur.fetchall():
        cancel_enrollment(cur, app["enrollment_id"], "ccmc: 72h claim window ended")
        cur.execute(
            "UPDATE charity_calendar_applications SET status='released', released_at=NOW() "
            "WHERE id=%s AND status=%s", (app["id"], app["status"]))
        # A Save-Ahead offer that lapses is released quietly: no spot to hand on.
        if not app["is_test"] and app["status"] == "invited":
            owner_alert(cur, f"Charity Calendar: {app['contact_name']} did not claim her spot",
                        f"{app['contact_name']} ({app['contact_email']}) did not claim her 2027 Charity "
                        f"Calendar spot within 72 hours, so it has been released. Open your review page to "
                        f"invite the next woman in line. {REVIEW_URL}")
        print(f"app {app['id']}: released (72h passed)")

    # 4. Stop invite reminders once she has claimed (or anything terminal).
    cur.execute(
        "SELECT a.id, a.enrollment_id, a.status FROM charity_calendar_applications a "
        "JOIN jhp_workflow_enrollments e ON e.id=a.enrollment_id "
        "WHERE e.workflow_id IN (%s,%s) AND e.status IN ('active','paused') AND a.status = ANY(%s)",
        (invite_wid, save_wid, list(TERMINAL)))
    for r in cur.fetchall():
        n = cancel_enrollment(cur, r["enrollment_id"], f"ccmc: application {r['status']}")
        print(f"app {r['id']}: invite reminders cancelled ({r['status']}, {n} row)")

    # 5. New applications -> owner alert (once each).
    cur.execute(
        "SELECT * FROM charity_calendar_applications WHERE owner_notified_at IS NULL "
        "AND is_test IS NOT TRUE ORDER BY id")
    for app in cur.fetchall():
        owner_alert(cur, f"New Charity Calendar application: {app['contact_name']}",
                    f"{app['contact_name']} applied for the 2027 Charity Calendar Model Call.\n"
                    f"Package: {PKG.get(app['package_interest'], app['package_interest'] or '-')}\n"
                    f"Payment: {PAY.get(app['payment_pref'], app['payment_pref'] or '-')}\n\n"
                    f"Review it here: {REVIEW_URL}")
        cur.execute("UPDATE charity_calendar_applications SET owner_notified_at=NOW() WHERE id=%s", (app["id"],))
        print(f"app {app['id']}: owner notified")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
