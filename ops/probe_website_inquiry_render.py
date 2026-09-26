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
  * each email carries exactly one photograph, with alt text and the width
    ATTRIBUTE Outlook needs -- without it Word draws the 1600px frame at its
    native size and the 600px card comes apart
  * the eight photographs are eight different frames, and every email keeps
    the JHP Boudoir logo header
  * every email ends on the Instagram sign-off, as an INLINE link under a rule
    and never as a second gold button competing with "Book my call"

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
    # The workflow name is what tells email_actions this is a marketing send and
    # so must carry the CAN-SPAM footer. Wrong name here and the probe would
    # pass while the real emails went out without it.
    'workflow': 'website_inquiry_2027',
    'contact': {'id': 'ghl_fake', 'name': 'Jessica Haslag',
                'first_name': 'Jessica', 'email': 'j@example.com',
                'phone': '5735550100'},
    'enrollment': {'id': 'fake', 'context': {'guide_url': GUIDE, 'calendar_url': CAL}},
    'session_date': None,
}

PART_ANCHORS = ('begin', 'worries', 'works', 'investment')
IG = 'https://www.instagram.com/jhpboudoir_'
# The card is 600px with 32px of padding either side.
IMG_WIDTH = '536'

fails = []
frames = {}


def check(cond, msg):
    if not cond:
        fails.append(msg)
    return cond


def main():
    b.check()
    print()
    for i, s in enumerate(b.STEPS, start=1):
        raw = b.body_of(s)
        cfg = {'subject': s['subject'], 'body_md': raw, 'sms': s['sms']}
        subj = wr.render_text(s['subject'], CTX, cfg)
        body = wr.render_text(raw, CTX, cfg)
        sms = wr.render_text(s['sms'], CTX, cfg)
        html = ea._md_to_html(body, ea._legal_footer_html(CTX))
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

        imgs = re.findall(r'<img [^>]*>', html)
        # The logo header is an <img> too, so the photograph is the other one.
        photos = [m for m in imgs if 'alt="JHP Boudoir"' not in m]
        check(len(imgs) == 2, f'{t}: expected a logo and one photograph, '
                              f'got {len(imgs)} image(s)')
        check(len(photos) == 1, f'{t}: {len(photos)} photograph(s), expected 1')
        if photos:
            pic = photos[0]
            check(f'width="{IMG_WIDTH}"' in pic,
                  f'{t}: the photograph has no width="{IMG_WIDTH}" -- Outlook '
                  f'will draw it at 1600px and break the layout')
            alt = re.search(r'alt="([^"]*)"', pic)
            check(alt is not None and len(alt.group(1)) > 10,
                  f'{t}: the photograph has no useful alt text')
            src = re.search(r'src="([^"]+)"', pic)
            if src:
                frame = src.group(1).rsplit('/', 1)[-1]
                check(frame not in frames,
                      f'{t}: frame {frame[:8]} already used in '
                      f'{frames.get(frame)}')
                frames[frame] = t
        # A logo header on every email, which is what makes them hers.
        check('alt="JHP Boudoir"' in html, f'{t}: the logo header is missing')

        # The Instagram sign-off: present, last, under a rule, and NOT a button.
        check(IG in html, f'{t}: the Instagram sign-off is missing')
        check('<hr' in html, f'{t}: the Instagram sign-off has no rule above it')
        ig_a = re.findall(r'<a [^>]*' + re.escape(IG) + r'[^>]*>', html)
        check(len(ig_a) == 1, f'{t}: {len(ig_a)} Instagram link(s), expected 1')
        if ig_a:
            check('background' not in ig_a[0],
                  f'{t}: the Instagram link rendered as a gold button -- it must '
                  f'stay inline so it does not compete with Book my call')
        check(html.rstrip().endswith('</table></div>'),
              f'{t}: the email does not end inside the branded container')

        # The compliance footer: the address, the reason, and a working opt-out.
        check(ea.STUDIO_ADDRESS in html, f'{t}: the postal address is missing')
        check(ea.STUDIO_NAME in html, f'{t}: the studio name is missing')
        check('unsubscribe/?c=' in html,
              f'{t}: the unsubscribe link is missing or carries no contact id')
        check('You are getting this because' in html,
              f'{t}: the footer does not say why she is receiving it')
        unsub_a = re.findall(r'<a [^>]*unsubscribe/[^>]*>', html)
        check(len(unsub_a) == 1, f'{t}: {len(unsub_a)} unsubscribe link(s), expected 1')
        if unsub_a:
            check('background' not in unsub_a[0],
                  f'{t}: the unsubscribe link rendered as a button')
        check(body.rstrip().endswith(IG + ')'),
              f'{t}: the Instagram sign-off is not the last thing in the body')

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
        print(f"   photo   : {re.search(r'media/([0-9a-f]{8})', html).group(1)}"
              f"  width={IMG_WIDTH}, logo header present")
        print(f"   sms     : {len(sms)} chars, ~{-(-len(sms) // 153)} segment(s)")

    print()
    check(len(frames) == len(b.STEPS),
          f'{len(frames)} distinct frame(s) across {len(b.STEPS)} emails')
    if fails:
        for f in fails:
            print('FAIL ', f)
        raise SystemExit(f"{len(fails)} check(s) failed")
    print('ALL RENDER CHECKS PASSED - nothing was sent')


if __name__ == '__main__':
    main()
