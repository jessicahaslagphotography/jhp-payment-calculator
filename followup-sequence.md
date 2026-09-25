# The follow-up sequence, for approval

**Status: DRAFT. Nothing is built and nothing is sending.**

Rewritten 25 September from Jessica's own Dubsado copy — the six-step
`inquiry_website` workflow sitting in Scalogy (`jhp_workflows`,
migration_status `mapped`, currently inactive). Her voice, her lines, her
energy. What changed is which facts it states and what each message is for.

---

## What her existing workflow does, and the two things wrong with it

`inquiry_website` fires six touches at 0, 3 days, 7 days, 14 days, 30 days
and 10 weeks. The cadence is almost exactly what she asked for — she wanted
24h, 72h, 7d, 14d, 1 month, 3 months and 6 months, which is her own schedule
plus a day-one nudge and a proper goodbye.

**All six steps send the identical 700-word email.** Not a variation — the
same body, six times, over ten weeks. That is a Dubsado artefact: it attached
the same questionnaire at each step. A woman who does not book gets the same
wall of text on day 3, day 7, day 14, day 30 and week 10. **That is the
single biggest improvement available here**, and it costs nothing: the same
touches, each doing a different job.

**And nine of its facts now contradict the site.** Her copy predates the
figures she settled on 24 September. This is the same drift that put $500 and
$2,800 in the Canva guide, in a second place nobody was looking.

| Her inquiry email says | The site says |
|---|---|
| 3–4 hour experience | **2–3 hours** |
| See your images **right after** your session | **7–14 business days later, over Zoom** |
| Collections as low as **$3,400** | Digital from **$1,250**, Full from $3,400 |
| Plans up to **18 months** in advance | **15 months** |
| Wardrobe sizes **S–4X** | **XS to 4X**, 160 pieces |
| Hair + makeup (reads as at the studio) | **at a local salon**, then she drives over |
| $697 session fee | ✅ matches |
| Tuesday and Thursday only | ✅ matches |

**Everything below uses the settled figures.** Where her line and the site
disagreed, the site won — that is the whole point of having settled them.

### The four open questions, answered 25 September

1. **"Most clients invest $5,600."** *Removed.* Not used anywhere.
2. **Klarna, Affirm, AfterPay and PayPal Credit.** *Still offered* — in
   message 5 now, as third-party and subject to credit approval, which is
   how she words it.
3. **"Plan set up within 7 days of booking, first payment due within 30
   days."** *Still the rule* — in message 5 now.
4. **Which floor to quote.** *"As low as $1,250."* Confirmed, which is what
   the draft already used and what the site says.

**Two of those facts are on the site NOWHERE.** The post-payment options and
the 7-day/30-day deadline are real terms of doing business with her, and
after this they will be stated in an email and in no other place she
controls. That is the shape of drift, not the shape of a settled figure — see
the FAQ note at the foot of this file.

---

## Before any of this can run

**1. The `Session Guide - Requested` tag still sends the old Canva PDF** —
$500 session fee, Collections from $2,800. Message 1 replaces it. This has to
change whether or not the rest is approved.

**2. There is no SMS consent on `/contact`.** It takes a phone number for a
guide and never asks permission to text. In the US that is TCPA exposure,
priced per message. **The emails can run today; the texts should wait** for
one line under the phone field:

> By giving your number you agree to receive texts from JHP Boudoir about
> your session. Message and data rates may apply. Reply STOP to opt out.

An hour's work — say the word.

**3. Exit conditions, or the sequence embarrasses her.** Remove from the
sequence the moment any of these happen:

| Trigger | Why |
|---|---|
| Books a consultation call | She is in the pre-call flow now |
| Session fee paid | Obvious, and the worst one to get wrong |
| Replies to any text or email | It is a conversation; automation stops |
| Unsubscribes, or replies STOP | Required, not optional |
| Tagged `Session Inquiry` (the `/inquire` form) | Further down the path; different sequence |

**4. The calendar only opens 4 days ahead.** Set at her instruction today. A
woman opening the month-3 email sees the next four days and nothing else.
Worth knowing when a six-month sequence keeps saying "book a call".

**5. Quiet hours 9am–8pm, her client's local time.** A 3am text from a
boudoir studio is a bad look.

---

## Links

    Guide     https://pages.scalogy.com/jhpboudoir1/session-guide/?n={{contact.first_name}}
    Calendar  https://api.leadconnectorhq.com/widget/booking/mi2EqYRq4gGEbBJHe82b

Deep links open that part of the guide on arrival: `#worries`, `#works`,
`#investment`.

**Her old workflow sent a hosted questionnaire** at
`view-form/?f=jhp-boudoir-experience-info-guide`. The Session Guide page
replaces it — same content, current figures, and it greets her by name.

**No prices in the emails except where marked.** The figures live in the FAQ,
the guide and the home page; a fourth copy in an inbox is a fourth thing to
update. Message 5 is the exception, because "what does it cost" deserves a
straight answer in the body.

---

# The messages

## 1 · Immediately

**Subject:** 🖤 You're in the right place

> Hi {{contact.first_name}}!
>
> I am **so** excited you reached out about a boudoir session with us at JHP
> Boudoir.
>
> Whether this is something you have been thinking about for years or you
> just had a little spark of *"maybe I could do this…"* — you are in the
> right place.
>
> And honestly? There are a lot of photographers you could have asked about
> this. You asked me. Thank you. That means more than you know. 💕
>
> Everything about the experience is right here — what is included, what it
> costs, how the day runs, and how to claim your spot on my calendar:
>
> **[Read your Session Guide →]**
>
> Your boudoir experience includes:
> ✨ A two to three hour experience in our luxury studio
> ✨ Professional hair and makeup at a local salon before you arrive (hellooooo makeover!)
> ✨ Full access to the studio wardrobe — 160 pieces, sizes XS to 4X
> ✨ A full session where I pose you from head to pointed toe
> ✨ Expert posing and expression guidance
> ✨ Retouching, and your private image reveal and ordering appointment
>
> **Ready to chat?** Grab a time and bring every question you have — the
> practical ones and the nervous ones. No pressure and no obligation. 🖤
>
> And if you already know you are ready to book — have a credit card handy!
> We will process your session fee retainer right on the call and get your
> booking finalized.
>
> **[Book my call →]**
>
> Take your time reading through it, and if you have questions I am just a
> message away.
>
> — Jess

**Text:**

> Hi {{contact.first_name}}! It's Jess at JHP Boudoir 🖤 So excited you
> reached out!
>
> Your Session Guide is here: [guide]
>
> There are plenty of photographers you could've asked — thank you for
> asking me!
>
> Questions or Ready to Book? Let's Chat: [calendar]
>
> Reply STOP to opt out.

*Three segments. The only message where that is worth it — guide, calendar,
thank-you and the compliance line.*

---

## 2 · 24 hours

**Subject:** Did your guide land?

> Hi {{contact.first_name}}!
>
> Just making sure the Session Guide reached you — it sometimes hides in your
> spam folder.
>
> **[Your Session Guide →]**
>
> And in case it helps to hear it: the thing women say most on that first
> call is some version of *"I'm not sure I'm the kind of person who does
> this."*
>
> Nearly every single one. You do not need to be brave, or in shape, or
> photogenic. You need to turn up — I will do the rest, and I will love
> every minute of it.
>
> Bring your questions and we will go through them together.
>
> **[Book my call →]**
>
> — Jess

**Text:**

> {{contact.first_name}}, just checking your Session Guide arrived — it
> sometimes hides in your spam folder! [guide]
>
> Any questions at all, reply right here 🖤 — Jess

---

## 3 · 72 hours

**Subject:** What if I'm nervous?

> Hi {{contact.first_name}},
>
> Totally normal. **Everyone** is.
>
> But nervous turns into empowered real quick, and you will leave feeling
> like a damn goddess. That is not a sales line — it is just what happens in
> that room.
>
> *"But I don't look like the women in your portfolio."*
>
> You do. The women in my galleries are teachers and nurses and mothers and
> grandmothers, and not one of them walked in feeling ready. What they had
> was two hours, professional hair and makeup, and someone telling them
> exactly what to do with their hands.
>
> > *"Jessica is amazing! Such a lovely day. She is so fun and
> > professional! She really makes the studio a safe and comfortable
> > place!"*
>
> **And what if I don't know how to pose?** You don't need to. That is
> literally my job. I guide you the entire time — hands, hips, face,
> everything.
>
> **[The things women worry about →]**
>
> **[Book my call →]**
>
> — Jess

**Text** *(optional — see the note on text volume)*:

> {{contact.first_name}}, the question everyone asks: "what if I'm nervous?"
>
> Totally normal. Everyone is. And you don't need to know how to pose — that's
> literally my job 🖤 [guide with #worries] — Jess

---

## 4 · 7 days

**Subject:** What your session day actually looks like

> Hi {{contact.first_name}}!
>
> Here is the whole thing, start to finish.
>
> **Hair and makeup first**, at a local salon — you drive over to the studio
> already done and gorgeous.
>
> **Then we photograph**, two to three hours, just the two of us. Be prepared
> to be sore afterwards. We do a lot of bending and twisting — it is quite
> the workout! 😅
>
> **Then you go home.** Your images come later, at a private Zoom
> appointment where we go through every one of them together, one at a time.
> You are never sent a link and left to figure it out on your own.
>
> That is the part women tell me afterwards was their favourite of the whole
> experience, and it is easily mine.
>
> **[How it all works →]**
>
> Questions about any of it? Bring them all.
>
> **[Book my call →]**
>
> — Jess

**Text:**

> {{contact.first_name}} — the bit most women are surprised by: you see your
> images WITH me, on a call. Never alone in an inbox 🖤
>
> How the day runs: [guide with #works] — Jess

---

## 5 · 14 days

**Subject:** Let's talk about the investment

> Hi {{contact.first_name}},
>
> I would much rather you knew before we talk than after. So, plainly:
>
> **The session fee is $697.** It is non-refundable, it reserves your date,
> and it covers everything in that list — the studio, hair and makeup, the
> wardrobe, the full session, retouching, and your reveal and ordering
> appointment.
>
> **Your images and products are purchased separately**, at your reveal.
> There are eight Collections. They start at **$1,250** for digital images
> and run to **$3,400 and up** for an album, all your digitals and a mobile
> app. Digitals, albums, prints, wall art — heirloom pieces meant to last a
> lifetime.
>
> **Got a little sticker shock?** Totally get it. Most of my clients feel
> that way at first. 🙌
>
> Here is the good news: you do not pay for everything at once. Every
> Collection is bought on an **interest-free prepayment plan** — biweekly or
> monthly, whichever suits you. Your plan is set up within 7 days of
> booking, and your first payment is due within 30 days. This is an
> investment in *you*, and I am here to make it as stress-free as I possibly
> can.
>
> **Prefer to pay afterwards?** Post-payment plans are available through
> third parties — Klarna, Affirm, AfterPay and PayPal Credit — subject to
> their credit approval.
>
> **[Every figure, written down →]**
>
> If a number raises a question, bring it. No pressure and no obligation.
>
> **[Book my call →]**
>
> — Jess

**Text** *(optional)*:

> {{contact.first_name}}, in case it's the question you haven't asked yet:
> session fee $697, Collections from $1,250, all on interest-free plans.
>
> Every figure: [guide with #investment] — Jess

---

## 6 · 1 month

**Subject:** Why women finally book

> Hi {{contact.first_name}},
>
> It is rarely a birthday — though a birthday is a wonderful reason.
>
> It is usually that they got tired of waiting to feel ready.
>
> > *"The confidence boost I had from this experience was unparalleled!"*
>
> > *"Jessica was fabulous from the very first contact to the image
> > reveal!"*
>
> If you are still thinking about it a month later, {{contact.first_name}} —
> that is generally your answer. And I would absolutely love to be the one
> you do it with. 🖤
>
> **[Book my call →]**
>
> — Jess

**Text:**

> {{contact.first_name}}, a month since your guide! Still thinking about it?
> That's usually the sign 🖤
>
> 20 minutes, bring your questions, no obligation: [calendar] — Jess

---

## 7 · 3 months

**Subject:** If you are waiting for the right time

> Hi {{contact.first_name}},
>
> Two practical things, in case they help you plan.
>
> **I photograph on Tuesdays and Thursdays only**, 9am to 3pm — so dates go
> sooner than people expect, and the studio books up to 15 months ahead.
>
> **And anything printed takes time.** An album or wall art is made to order
> and arrives within six weeks of your reveal, which is itself a week or two
> after your session.
>
> So if you want your images *for* something — a birthday, an anniversary, a
> date that matters — work backwards from it. I am very happy to help you do
> exactly that on a call.
>
> **[Book my call →]**
>
> — Jess

**Text** *(optional)*:

> {{contact.first_name}}, planning note: I shoot Tue/Thu only, and albums
> take ~6 weeks after your reveal. Want images for a date? Work backwards!
>
> [calendar] — Jess

---

## 8 · 6 months

**Subject:** Last note from me 🖤

> Hi {{contact.first_name}},
>
> This is the last one I will send unless you tell me otherwise. I would
> rather leave the door open than keep knocking on it.
>
> Thank you for thinking of my studio in the first place. With everywhere
> you could have looked, that still means a great deal to me.
>
> **[Your Session Guide — yours to keep →]**
>
> And if the time ever comes, I am right here:
>
> **[Book my call →]**
>
> I hope you do it one day, {{contact.first_name}}. With me or without me —
> you deserve to see yourself the way other people do.
>
> — Jess

**Text:**

> {{contact.first_name}}, last message from me 🖤 Your guide is yours to
> keep [guide], and the door stays open whenever you're ready.
>
> Thank you for thinking of my studio. — Jess

---

## Notes on the writing

**The voice is hers, lifted from her own inquiry email.** "I'm so excited you
reached out", "hellooooo makeover", "totally normal, everyone is", "nervous
turns into empowered real quick", "you'll leave feeling like a damn goddess",
"got a little sticker shock? totally get it", "that's literally my job". The
earlier draft was far too restrained — this is how she actually writes, and
it is better.

**Each message has one job.** Welcome, reassure, name the fear, explain the
day, talk money, prove it, help her plan, then leave. Her Dubsado version
sent one message six times; this is the same cadence doing six different
things.

**The thank-you is in message 1 and message 8 and nowhere between.** Her
note: *"there are many choices for a boudoir photographer and I appreciate
them choosing to inquire with my studio."* In all eight it stops reading as
gratitude and starts reading as a tic.

**Energy everywhere except where it would be tone-deaf.** Messages 1, 2, 4,
5 and 6 are bright. Message 3 is warm but steady — it is answering a woman
who thinks she is not good enough to be photographed. Message 8 is a
goodbye. Emoji and exclamation marks in either would read as not listening.

**Three texts are marked optional.** Eight in six months is comfortable;
three inside a fortnight is a lot from a photographer she has not met. Cut
them and the text sequence is five, which reads as attentive rather than
insistent.

**The reviews are real.** Message 3 uses Miss H., unplaced on the site — see
`reviews.md`. Message 6 uses two lines from the Portfolio and The Experience.
The one-review-one-page rule in `CLAUDE.md` is about the website; re-using
them in email is fine and worth knowing rather than discovering.

**What is deliberately not here:** a discount, an artificial deadline, and a
"spots are filling up". She runs none of those, and manufacturing urgency for
a woman deciding whether to be photographed in her underwear is the wrong
instinct. (The 7-day plan deadline in message 5 is a real term of business,
not a pressure tactic.)

---

## One thing left: these two facts belong on the site too

Message 5 now states two things the website does not say anywhere:

- a payment plan is **set up within 7 days of booking, first payment within
  30 days**
- **post-payment plans** through Klarna, Affirm, AfterPay and PayPal Credit

Both are Jessica's, both confirmed current on 25 September. But a term of
business that lives in an email and nowhere else is the drift this project
keeps finding: the Canva guide, her Dubsado emails, and now this. `CLAUDE.md`
is explicit that **every figure lives in the FAQ**.

The FAQ's payment answer currently reads:

> Yes, and every collection is bought through one. You set yours up when you
> book, and pay weekly, biweekly or monthly — whichever suits you.
>
> They are interest free. It is the same figure either way, spread out. You
> may book your session up to 15 months in advance.

**Proposed, for her approval** — two sentences added, nothing removed:

> Yes, and every collection is bought through one. You set yours up within
> seven days of booking and pay weekly, biweekly or monthly — whichever
> suits you. Your first payment is due within thirty days.
>
> They are interest free. It is the same figure either way, spread out. You
> may book your session up to 15 months in advance.
>
> If you would rather pay after your session, post-payment plans are
> available through Klarna, Affirm, AfterPay and PayPal Credit, subject to
> their credit approval.

That is one generator, one template patch and one page render. **Not done —
it is a deadline and a set of named third parties on a live client-facing
page, which is hers to approve, not mine to assume.**
