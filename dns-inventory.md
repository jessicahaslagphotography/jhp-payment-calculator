# jhpboudoir.com DNS as it stands, 26 September 2026

Transcribed from Jessica's Squarespace screenshots before any change is made.
**This file is the rollback.** If a record is deleted or edited by mistake,
what it said is here. Nothing in this file has been changed by anybody; it is
a photograph of the zone on the morning of the cutover.

## The two records that change at launch, and nothing else

    A      @      141.193.213.10    30 mins    Showit   -> DELETE
    A      @      141.193.213.11    30 mins    Showit   -> DELETE
                                               -> one A @ to Netlify's IP

    CNAME  www    wp.wpenginepowered.com   30 mins     -> EDIT to Netlify

**BOTH apex A records must go.** They are a pair, and deleting one and editing
the other leaves the domain round-robining between Netlify and Showit -- about
half of visitors would keep seeing the old site, intermittently, which looks
like a caching problem and is not one.

**TTL on all three is 30 minutes**, which is the good news: the cutover takes
about half an hour to spread, and so does putting it back.

## Everything else is left alone

### A -- her Scalogy pages
    A      boudoirgiveaway   178.105.37.93   30 mins
    A      reserve           178.105.37.93   4 hrs
    A      reserved          178.105.37.93   4 hrs

These three are Scalogy's IP written out, where the other fifteen Scalogy
subdomains are CNAMEs to `pages.scalogy.com`. Both work. The CNAME is the
sturdier form -- if Scalogy ever moves that IP, the CNAMEs follow and these
three break. Worth tidying one day, not today, and not in the same pass as a
domain cutover.

### CNAME -- Scalogy pages
    emc-retainer      pages.scalogy.com
    everybody         pages.scalogy.com
    finalsale         pages.scalogy.com
    flashsale         pages.scalogy.com
    giveawaydetails   pages.scalogy.com
    modelrelease      pages.scalogy.com
    reservedemc       pages.scalogy.com
    reveal            pages.scalogy.com
    treehouse         pages.scalogy.com
    updatecard        pages.scalogy.com
    welcomeemc        pages.scalogy.com

### CNAME -- email and other services
    email.send        mailgun.org
    fde._domainkey    dkim.r9vkbs.fd78.fdske.com      Flodesk DKIM
    fdesp             spf.r9vkbs.fd78.fdske.com       Flodesk SPF
    go                sites.ludicrous.cloud           UNIDENTIFIED - ask Jessica
    _domainconnect    _domainconnect.domains.squarespace.com   (preset)

### MX -- her email. NONE OF THESE MOVE.
    @      1    aspmx.l.google.com          Google Workspace
    @      5    alt1.aspmx.l.google.com
    @      5    alt2.aspmx.l.google.com
    @      10   alt3.aspmx.l.google.com
    @      10   alt4.aspmx.l.google.com
    send   10   mxa.mailgun.org             Mailgun, for send.jhpboudoir.com
    send   10   mxb.mailgun.org

### TXT
    _dmarc                 v=DMARC1; p=none
    _dmarc.send            v=DMARC1;p=none;
    krs._domainkey.send    k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQK...
    send                   v=spf1 include:spf.leadconnectorhq.com
                           include:mailgun.o...

## THERE IS NO SPF RECORD ON THE ROOT DOMAIN, and that is a real gap

Her mailbox is Google Workspace (the five `aspmx.l.google.com` MX records on
`@`), and there is **no `v=spf1` TXT on `@`** -- only on `send`, which is the
Mailgun/LeadConnector subdomain the automations send from. So every email from
`jessica@jhpboudoir.com` goes out with nothing telling the receiving server
that Google is allowed to send as her domain.

`_dmarc` is `p=none`, so nothing is being rejected today and this is not an
emergency. But Gmail and Yahoo have required SPF and DKIM of bulk senders since
2024, and a domain with a DMARC record and no SPF at the apex is the shape that
starts landing in spam.

The fix is **one TXT record** and it has nothing to do with the launch:

    TXT    @    v=spf1 include:_spf.google.com ~all

**Do not add it in the same sitting as the cutover.** One change at a time, so
that if something goes wrong it is obvious which change did it. This one is
worth doing the week after.

(Google Workspace DKIM is also worth checking in the admin console -- the
`fde._domainkey` record here is Flodesk's, not Google's.)

## The blog turns out to be easy

`www` points at `wp.wpenginepowered.com`, which means **the WordPress install
is already reachable on its own at WP Engine** -- Showit is proxying `/blog/`
through to it. So the blog does not need migrating anywhere:

    CNAME  blog   wp.wpenginepowered.com

...plus asking WP Engine (or Showit support) to add `blog.jhpboudoir.com` to
that install so it answers on the new name. **Do this BEFORE the cutover**,
while the blog is still up, so there is no window where it is unreachable. Then
`deploy-site.py --blog-url https://blog.jhpboudoir.com/` redirects `/blog/*`
there and puts the Blog link back in all nine footers.
