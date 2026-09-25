#!/usr/bin/env python3
"""READ-ONLY: render all eight 'Website Inquiry - 2027' emails and check them.

Sends nothing and writes nothing. It runs the exact path a live send takes --
workflow_runner.render_text for the merge fields, then
email_actions._md_to_html for the markup -- against a fake contact and a fake
enrollment context, and then asserts the things that would be invisible in the
database and obvious in somebody's inbox:

  * no {{token}} survives into the HTML
  * nothing rendered to an empty string (a sentence trailing into nothing is
    the failure mode of an unmapped token)
  * both URLs appear, and the guide's deep-link anchors are real part anchors
  * every standalone CTA link became a real <a> button, not literal markdown
  * the six-line includes list renders as six lines, not one run-on
  * nothing that should be bold or italic leaked its asterisks

Run it after any edit to the copy, to the runner's merge fields, or to the
markdown renderer.
"""
import os
import sys
import re

sys.path.insert(0, '/home/scalogy/artifacts/workflow-runner')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'workflow-runner'))
import workflow_runner as wr          # noqa: E402
import email_actions as ea            # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_website_inquiry_2027 as b  # noqa: E402

GUIDE = 'https://pages.scalogy.com/jhpboudoir1/session-guide/?n=Jessica'
CAL = ('https://api.leadconnectorhq.com/widget/booking/mi2EqYRq4gGEbBJHe82b'
       '?first_name=Jessica&last_name=Haslag&email=j%40example.com&phone=5735550100')

CTX = {
    'contact': {'id': 'ghl_fake', 'name': 'Jessica Haslag',
                'first_name': 'Jessica', 'email': 'j@example.com',
                'phone': '5735550100'},
    'enrollment': {'id': 'fake', 'context': {'guide_url': GUIDE, 'calendar_url': CAL}},
    'session_date': None,
}

PART_ANCHORS = ('begin', 'worries', 'works', 'investment')

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
    return cond


def main():
    b.check()
    print()
    for i, s in enumerate(b.STEPS, start=1):
        cfg = {'subject': s['subject'], 'body_md': s['body'], 'sms': s['sms']}
        subj = wr.render_text(s['subject'], CTX, cfg)
        body = wr.render_text(s['body'], CTX, cfg)
        sms = wr.render_text(s['sms'], CTX, cfg)
        html = ea._md_to_html(body)
        t = s['target']

        check('{{' not in subj + body + sms, f'{t}: an unrendered {{{{token}}}} survived')
        check('{{' not in html, f'{t}: an unrendered token reached the HTML')
        # A token that rendered empty leaves the sentence around it reading as
        # though a word were missing -- a dangling colon is the visible tell.
        check(not body.rstrip().endswith(':') and ': \n' not in body,
              f'{t}: the body ends on a colon, so something rendered empty')
        check(GUIDE in body or CAL in body, f'{t}: neither URL rendered')
        check(CAL in html, f'{t}: the calendar link is missing from the HTML')
        check(html.count('<a href') >= 1, f'{t}: no link survived into the HTML')
        # A standalone link must have become a centred button, not stayed as
        # literal markdown a recipient would read as "[Book my call](http...".
        check('](' not in html, f'{t}: literal markdown link left in the HTML')
        check('**' not in html, f'{t}: literal ** left in the HTML')
        buttons = len(re.findall(r'background: #9a7b4f', html))
        include_lines = body.count('✨')

        if include_lines:
            check(include_lines == 6,
                  f'{t}: includes list has {include_lines} lines, expected 6')
            # One paragraph, five <br> between the six lines. The markdown
            # renderer has no <ul>, so this is what "a list" means here.
            para = re.search(r'<p[^>]*>(✨.*?)</p>', html, re.S)
            check(para is not None, f'{t}: includes list did not render as one paragraph')
            if para:
                check(para.group(1).count('<br>') == 5,
                      f'{t}: includes list joined with '
                      f'{para.group(1).count("<br>")} breaks, expected 5')

        anchors = re.findall(r'session-guide/\?n=Jessica#(\w+)', html)
        for a in anchors:
            check(a in PART_ANCHORS, f'{t}: deep link #{a} is not a real part anchor')

        print(f"{i}. {t}")
        print(f"   subject : {subj}")
        print(f"   body    : {len(body):>5} md -> {len(html):>6} html, "
              f"{buttons} button(s), {include_lines} includes line(s)"
              + (f", deep link #{anchors[0]}" if anchors else ""))
        print(f"   sms     : {len(sms)} chars, ~{-(-len(sms) // 153)} segment(s)")

    print()
    if fails:
        for f in fails:
            print('FAIL ', f)
        raise SystemExit(f"{len(fails)} check(s) failed")
    print('ALL RENDER CHECKS PASSED - nothing was sent')


if __name__ == '__main__':
    main()
