# The follow-up sequence, for approval

**Status: DRAFT. Nothing here is built and nothing is sending.** Jessica
asked for this on 25 September and asked to approve before it goes live.

What triggers it: a woman fills in the form on `/contact`. That already
tags her **`Session Guide - Requested`** in GHL and already forwards her
straight to the booking calendar. Everything below is what happens after.

---

## Before any of this can run

Four things need settling. The first two are blockers.

### 1. The tag still sends the old Canva PDF — BLOCKER

The GHL workflow watching `Session Guide - Requested` sends the superseded
magazine: **$500 session fee, Collections from $2,800**. That undercuts the
live site by $197 and $1,550. Every woman who has filled in that form has
had the wrong prices.

Message 1 below replaces it with the link. **This has to change whether or
not the rest of the sequence is approved.**

### 2. There is no SMS consent on the form — BLOCKER for the texts

`/contact` collects first, last, email, phone. It does not ask permission
to text. In the US, automated marketing texts to a number collected
without express written consent is TCPA exposure, and the penalties are
per message.

The emails can run today. **The texts should not run until the form
carries a consent line.** One sentence under the phone field does it, for
example:

> By giving your number you agree to receive texts from JHP Boudoir about
> your session. Message and data rates may apply. Reply STOP to opt out.

That is a form change, a rebuild and a republish — an hour's work. Say the
word and it is done.

### 3. The calendar only allows booking 4 days ahead

Set on 25 September at Jessica's instruction. It means a woman opening the
month-3 email sees the next four days and nothing else.

That may be exactly right — it creates urgency and protects her diary. But
it is worth knowing that a "book your call" button in a six-month sequence
is showing a four-day window. If a woman is planning around an occasion
next spring, she cannot book that far out from any of these emails.

### 4. Exit conditions must exist before the first send

Without these the sequence embarrasses her. A woman who booked and paid on
Tuesday must not get "still thinking about it?" on Thursday.

**Remove from the sequence the moment any of these happen:**

| Trigger | Why |
|---|---|
| Books a consultation call | She is in the pre-call flow now, not the nurture |
| Session fee paid / becomes a client | Obvious, and the worst one to get wrong |
| Replies to any text or email | It is a conversation; automation stops |
| Unsubscribes, or replies STOP | Required, not optional |
| Tagged `Session Inquiry` (the `/inquire` form) | She has moved further down; different sequence |

---

## The shape of it

Eight touchpoints over six months. Each one has a job — none of them is
"just checking in" a second time.

| When | The job it does | Email | Text |
|---|---|---|---|
| Immediately | Deliver the guide | yes | yes |
| 24 hours | Did it land, and the first fear | yes | yes |
| 72 hours | "I don't look like those women" | yes | *optional* |
| 7 days | What the day actually looks like | yes | yes |
| 14 days | What it costs, plainly | yes | *optional* |
| 1 month | Why women finally book | yes | yes |
| 3 months | Planning and timing | yes | *optional* |
| 6 months | The door stays open | yes | yes |

**Three texts are marked optional.** Eight texts in six months is
comfortable; eight texts where three land within a fortnight is a lot from
a photographer she has not met. Cut them and the text sequence is five,
which reads as attentive rather than insistent. Her call.

**Quiet hours: 9am to 8pm, her client's local time.** GHL enforces this
per workflow. A 3am text from a boudoir studio is a bad look.

---

## Links used throughout

    Guide     https://pages.scalogy.com/jhpboudoir1/session-guide/?n={{contact.first_name}}
    Calendar  https://api.leadconnectorhq.com/widget/booking/mi2EqYRq4gGEbBJHe82b

The guide greets her by name from that `?n=` parameter — three places, and
nowhere else, so it does not read like a mail merge. **Always send the link
with the parameter on it.**

Deep links open the relevant part of the guide on arrival:

    #works       How It All Works
    #investment  The Investment
    #worries     The Things Women Worry About

**No prices in any email.** The figures live in the FAQ, the guide and the
home page — a fourth copy in an email sequence is a fourth thing to change
on the day a price moves, and a stale price in somebody's inbox is exactly
how the Canva guide went wrong. Every message links to the guide instead.

---

# The messages

## 1 · Immediately

**Subject:** Your Session Guide is here — and thank you

> Hi {{contact.first_name}},
>
> I am so glad you reached out.
>
> There are a lot of photographers you could have asked about this, and you
> asked me. That genuinely means something, and I do not take it lightly.
>
> So — here is your Session Guide. What a boudoir session here is really
> like, how the day runs, what the studio is like, and every question women
> ask me before they book.
>
> **[Read your Session Guide]**
>
> The other half of this is a twenty minute phone call with me. Bring every
> question you have — the practical ones and the nervous ones. No pressure
> and no obligation, I promise.
>
> **[Book my call]**
>
> I cannot wait to talk to you.
>
> — Jess

**Text:**

> Hi {{contact.first_name}}! Jess here at JHP Boudoir — so glad you reached
> out.
>
> Your Session Guide: [guide]
>
> There are plenty of photographers you could have asked, and you asked me.
> Thank you!
>
> Questions? Let's talk: [calendar] — no pressure, no obligation.
>
> Reply STOP to opt out.

*This one runs to about three segments. It is the only message where that is
worth it — it carries the guide, the calendar, the thank-you and the
compliance line.*

---

## 2 · 24 hours

**Subject:** Did your guide arrive?

> Hi {{contact.first_name}},
>
> Just making sure it landed — these sometimes hide in Promotions.
>
> **[Your Session Guide]**
>
> And in case it helps: the thing women say most on that first call is some
> version of *"I'm not sure I'm the kind of person who does this."* Nearly
> everyone says it. You do not need to be brave, or in shape, or
> photogenic. You need to turn up. I will do the rest, and I will love
> every minute of it.
>
> Bring your questions and we will go through them together.
>
> **[Book my call]**
>
> — Jess

**Text:**

> {{contact.first_name}}, just checking your Session Guide arrived — it
> sometimes hides in Promotions! [guide]
>
> Any questions at all, reply right here. — Jess

---

## 3 · 72 hours

**Subject:** "I don't look like the women in your portfolio"

> Hi {{contact.first_name}},
>
> That is the sentence I hear most, and it is almost always wrong.
>
> The women in my galleries are teachers and nurses and mothers and
> grandmothers. Not one of them arrived feeling ready. What they had was
> two hours, professional hair and makeup, and someone telling them exactly
> what to do with their hands.
>
> > *"Jessica is amazing! Such a lovely day. She is so fun and
> > professional! She really makes the studio a safe and comfortable
> > place!"*
>
> If that is the thing holding you back, bring it to the call. It is
> genuinely my favourite thing to talk about.
>
> **[Book my call]**
>
> — Jess

**Text** *(optional — see above)*:

> {{contact.first_name}}, the thing nearly everyone says first: "I don't
> look like the women in your portfolio."
>
> You do. That's rather the point. [guide with #worries] — Jess

---

## 4 · 7 days

**Subject:** What your session day actually looks like

> Hi {{contact.first_name}},
>
> Here is the whole thing, start to finish.
>
> Hair and makeup first, at a local salon — so you arrive at the studio
> already done. We photograph for two to three hours. Then you go home.
>
> Your images come later, at a private Zoom appointment where we go through
> every one of them together. You are never sent a link and left to figure
> it out on your own. That is the part women tell me afterwards was their
> favourite of the whole experience, and it is easily mine.
>
> **[How it all works →]**
>
> Questions about any of it? Bring them all.
>
> **[Book my call]**
>
> — Jess

**Text:**

> {{contact.first_name}} — the bit most women are surprised by: you see
> your images WITH me, on a call. Never alone in an inbox.
>
> Here's how the day runs: [guide with #works] — Jess

---

## 5 · 14 days

**Subject:** What it costs, plainly

> Hi {{contact.first_name}},
>
> I would much rather you knew before we talk than after.
>
> There is a session fee, which reserves your date. Your images are
> purchased separately, at your reveal. There are eight Collections — the
> smallest is digital images, the largest is an album, all your digitals
> and a mobile app — and you choose which one when you book, on an
> interest-free plan.
>
> Every figure is written down here, so nothing on the call is a surprise:
>
> **[The Investment →]**
>
> And if a number raises a question, bring it. No pressure and no
> obligation.
>
> **[Book my call]**
>
> — Jess

**Text** *(optional)*:

> {{contact.first_name}}, in case it's the question you haven't asked yet:
> every price is written down, right here. [guide with #investment]
>
> No surprises on the call. — Jess

---

## 6 · 1 month

**Subject:** Why women finally book

> Hi {{contact.first_name}},
>
> It is rarely a birthday — though a birthday is a wonderful reason.
>
> It is usually that they got tired of waiting to feel ready.
>
> > *"The confidence boost I had from this experience was
> > unparalleled!"*
>
> > *"Jessica was fabulous from the very first contact to the image
> > reveal!"*
>
> If you are still thinking about it a month later, that is generally your
> answer. And I would love to be the one you do it with.
>
> **[Book my call]**
>
> — Jess

**Text:**

> {{contact.first_name}}, a month since your guide! Still thinking about
> it? That's usually the sign.
>
> 20 minutes, bring your questions, no obligation: [calendar] — Jess

---

## 7 · 3 months

**Subject:** If you are waiting for the right time

> Hi {{contact.first_name}},
>
> Two practical things, in case they help you plan.
>
> I photograph on Tuesdays and Thursdays, so dates go sooner than people
> expect. And anything printed — an album, wall art — takes up to six weeks
> after your reveal, which is itself a week or two after your session.
>
> So if you want your images *for* something, work backwards from that
> date. I am very happy to help you do exactly that on a call.
>
> **[Book my call]**
>
> — Jess

**Text** *(optional)*:

> {{contact.first_name}}, one planning note: I shoot Tue/Thu only, and
> albums take ~6 weeks after your reveal. If you want images for a date,
> work backwards! [calendar] — Jess

---

## 8 · 6 months

**Subject:** Last note from me

> Hi {{contact.first_name}},
>
> This is the last one I will send unless you tell me otherwise. I would
> rather leave the door open than keep knocking on it.
>
> Thank you for thinking of my studio in the first place. With everywhere
> you could have looked, that still means a great deal to me.
>
> The guide is yours to keep, whenever you want it:
>
> **[Your Session Guide]**
>
> And if the time ever comes, I am right here:
>
> **[Book my call]**
>
> I hope you do it one day, {{contact.first_name}} — with me or without me.
>
> — Jess

**Text:**

> {{contact.first_name}}, last message from me. Your guide is yours to keep
> [guide], and the door stays open whenever you are ready.
>
> Thank you for thinking of my studio. — Jess

---

## Notes on the writing

**Every message has one job.** Reassure, then name the fear, then explain
the process, then the money, then proof, then timing, then leave. Nothing
says "just checking in" twice, because that is what makes a sequence feel
automated.

**The thank-you is in message 1 and message 8, and nowhere in between.**
Jessica's note, 25 September: *"there are many choices for a boudoir
photographer and I appreciate them choosing to inquire with my studio."* It
opens the sequence and it closes it. Put it in all eight and it stops
reading as gratitude and starts reading as a tic.

**"Bring your questions" replaced "nothing to prepare".** Her note, same
day: *"Ask them to bring any questions they may have during this call. No
pressure or obligation."* It is a better line because it gives her
something to DO — a woman who has been told there is nothing to prepare
still turns up not knowing what to ask. **The same phrase was live in two
other places** and both were changed in the same pass: the guide's closing
band and the GHL calendar's own description.

**Upbeat, but not everywhere.** Messages 1, 2, 4 and 6 carry the energy —
she is pleased, and it should read that way. Messages 3 and 8 deliberately
do not. Three is answering a woman who thinks she is not good enough to be
photographed, and eight is a goodbye; brightness in either would read as
not listening. Warmth is not the same thing as exclamation marks, and the
difference matters most exactly where the subject is tender.

**The 6-month message is the one that gets replies.** Sequences that end by
giving permission to go tend to hear back from people who would never have
answered anything else. It is also simply the decent way to finish.

**The reviews are real and are hers.** Message 3 uses Miss H., unplaced on
the site — see `reviews.md`. Message 6 uses two lines that are on the
Portfolio and The Experience. The one-review-one-page rule in `CLAUDE.md`
is about the website; re-using them in email is fine, and worth knowing
rather than discovering.

**What is deliberately not here:** a discount, a deadline, and a "spots are
filling up". She has none of those running, and inventing urgency for a
woman deciding whether to be photographed in her underwear is the wrong
instinct.
