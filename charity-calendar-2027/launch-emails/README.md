# CCMC 2027 launch-week emails (set up 2026-10-24 evening CT)

Copy source: Claude Doc "Charity Calendar Model Call — Launch Week Campaign (Oct 26–30)".

## What is live
- **GHL email templates** (Marketing > Emails > Templates), created by `ops/ccmc_launch_emails.py --templates`:
  | # | Template | GHL id |
  |---|---|---|
  | 1 | CCMC 2027 - 1 Sun VIP early access (past clients) | 6add6ee9861298b3de22df5e |
  | 2 | CCMC 2027 - 2 Mon Announcement | 6add6eeb7df95f009f0f68b3 |
  | 3 | CCMC 2027 - 3 Tue The why | 6add6eed421aad960c76c86f |
  | 4 | CCMC 2027 - 4 Wed Proof | 6add6eee861298b3de22df7d |
  | 5 | CCMC 2027 - 5 Thu Questions | 6add6eef861298b3de22df83 |
  | 6 | CCMC 2027 - 6 Fri Last call | 6add6ef0768aca1343232436 |
- Each email: Model Call graphic N (GHL media > Charity Calendar Graphics > Model Call Graphics, `N.png`),
  a before/after (`Before and After Posts (N+2).png`), the Apply button, and a "Join the private VIP group"
  button (facebook.com/groups/1107773373084834). Hidden preheader = the preview text.
- **Sunday past-client send** goes through jhp-workflow-runner, not a GHL campaign (the API cannot schedule
  campaigns): jhp workflow `ccmc_launch_week` (id 082762b7-399e-4ba5-adbf-cbeede545d59), step 1 holds the
  rendered email. 164 enrollments due 2026-10-25 14:00Z (9 AM CT); the runner sends 100 per 5-minute pass.
  `ccmc_launch_week` was added to `MARKETING_WORKFLOWS` in workflow-runner/email_actions.py, so it carries
  the CAN-SPAM footer and honours email_optouts.
- Enrollment (`ops/ccmc_launch_enroll.py --past`) re-resolves every contact in GHL by email (the local
  mirror had a stale id for Jessica) and tags them `ccmc-early-access`.

## To change Sunday's copy before it sends
Edit `ops/ccmc_launch_emails.py`, then run workflow `ccmc-launch-emails` (rewrites the runner step and the
GHL templates). The runner reads the step at send time.

## Mon–Fri
Scheduled by Jessica in GHL as campaigns from templates 2–6, 9:00 AM CT, excluding tag
"Charity Calendar 2027 - Applied".
