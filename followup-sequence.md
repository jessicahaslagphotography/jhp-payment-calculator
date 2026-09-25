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
> There are a lot of photographers you could have asked about this. You asked
> me. Thank you. That means more than you know. 💕
>
> Everything about the experience is right here — what is included, what it
> costs, how the day runs, and how to claim your spot on my calendar:
>
> **[Read your Session Guide →]**
>
> Your boudoir experience includes:
>
> - ✨ A two to three hour experience in our luxury studio
> - ✨ Professional hair and makeup at a local salon before you arrive (hellooooo makeover!)
> - ✨ Full access to the studio wardrobe — 160 pieces, sizes XS to 4X
> - ✨ A full session where I pose you from head to pointed toe
> - ✨ Expert posing and expression guidance
> - ✨ Retouching, and your private image reveal and ordering appointment
>
> **Ready to chat?** Grab a time and bring every question you have — the
> practical ones and the nervous ones. No pressure and no obligation. 🖤
>
> And if you already know you are ready to book — have a credit card handy!
> We will process your session fee retainer right on the call and get your
> booking started.
>
> **[Book my call →]**
>
> Take your time reading through it, and if you have questions I am just a
> message away.
>
> — Jess

**Text:**

> Hi {{contact.first_name}}! It's Jess at JHP Boudoir. I am so excited you
> reached out about a boudoir session!
>
> Everything about the experience is right here — what's included, what it
> costs and how the day runs: [guide]
>
> There are plenty of photographers you could've asked — thank you for
> inquiring with my studio!
>
> Questions or Ready to Book? Let's Chat: [calendar]
>
> Reply STOP to opt out.

*Four segments. The only message where that is worth it — guide, calendar,
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
> photogenic. You just need to show up — I will do the rest, and you will
> love every minute of it. This is a full service boudoir studio, and I will
> take great care of you throughout your boudoir experience.
>
> Bring your questions and we will go through them together.
>
> **[Book my call →]**
>
> — Jess

**Text:**

> Hey, {{contact.first_name}}! Just checking to see if your session guide
> arrived? It sometimes hides in your spam folder! [guide]
>
> You do not need to be brave, or in shape, or photogenic — you just need to
> show up. This is a full service boudoir studio and I will take great care
> of you the whole way through.
>
> Any questions at all, reply right here or book a call! Talk soon!
>
> [calendar] — Jess

---

## 3 · 72 hours

**Subject:** What if I'm nervous?

> Hi {{contact.first_name}},
>
> Totally normal to be nervous. **Everyone** is.
>
> But nervous turns into empowered real quick, and you will leave feeling
> like a damn goddess. That is just what happens in my studio.
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

**Text:**

> {{contact.first_name}}, the question everyone asks me: "what if I'm
> nervous?"
>
> Totally normal to be nervous. Everyone is! And you don't need to know how
> to pose — that is literally my job. I guide you the entire time.
>
> Being nervous is the best reason there is to book the call. Bring every
> worry you have and we will talk it all the way through — no pressure and
> no obligation.
>
> Let's get you on the phone: [calendar]
>
> — Jess

---

## 4 · 7 days

**Subject:** What your session day actually looks like

> Hi {{contact.first_name}}!
>
> It has been a week since you inquired with the studio, and I would love to
> get your call on the books! So here is the whole thing, start to finish.
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
> Questions about any of it? Bring them all. Let's get you booked!
>
> **[Book my call →]**
>
> — Jess

**Text:**

> {{contact.first_name}}, it's been a week since you inquired with the
> studio! Have you had a chance to read through your Session Guide yet?
> [guide]
>
> Hair and makeup first at a local salon, then two to three hours in the
> studio, then your images at a private Zoom reveal where we go through
> every one together. You are never sent a link and left to figure it out on
> your own.
>
> Any questions I can answer for you? Let's get your call booked: [calendar]
>
> — Jess

---

## 5 · 14 days

**Subject:** Let's talk about the investment

> Hi {{contact.first_name}},
>
> It has been two weeks since you reached out to the studio, so I wanted to
> check in with you again!
>
> And I would much rather you knew what this costs before we talk than
> after. So, plainly:
>
> **The session fee is $697.** It is non-refundable, it reserves your date,
> and it covers everything — the studio, hair and makeup, the wardrobe, the
> full session, retouching, and your reveal and ordering appointment.
>
> **Your images and products are purchased separately**, at your reveal.
> Digital Collections begin at **$1,250**, and Full Collections — album,
> digitals, mobile app, wall art and more — begin at **$3,400**. There are
> eight in all, so there is room to find the one that fits.
>
> **Got a little sticker shock?** Totally get it. Most of my clients feel
> that way at first. 🙌
>
> Here is the good news: you do not pay for it all at once. Every Collection
> is bought on an **interest-free prepayment plan** — weekly, biweekly or
> monthly, whichever suits you. Your plan is set up within 7 days of
> booking, and your first payment is due within 30 days.
>
> And you can book your session **up to 15 months in advance**, which matters
> more than it sounds. The further out your date, the more payments your plan
> spreads across — and that is what keeps the amount manageable for most
> women.
>
> **[Every figure, written down →]**
>
> If a number raises a question, bring it. No pressure and no obligation!
> Let's get on the phone and work through any questions you have!
>
> **[Book my call →]**
>
> — Jess

**Text:**

> {{contact.first_name}}! It's been two weeks since you reached out. I just
> sent over everything about the investment — the session fee, the
> Collections and the interest-free payment plans, all written down.
>
> And you can book up to 15 months out, so your plan spreads across as many
> payments as you need to keep it manageable.
>
> If a number raises a question, bring it. No pressure and no obligation!
>
> I would absolutely love to get your session on the books. Let's find a
> time to chat: [calendar]
>
> — Jess

---

## 6 · 1 month

**Subject:** I haven't forgotten about you 🖤

> Hi {{contact.first_name}},
>
> It has been a month since you reached out — and I have not forgotten about
> you!
>
> Here is the thing about why women finally book. It is rarely a birthday,
> though a birthday is a wonderful reason. It is usually that they got tired
> of waiting to feel ready.
>
> > *"The confidence boost I had from this experience was unparalleled!"*
>
> > *"Jessica was fabulous from the very first contact to the image
> > reveal!"*
>
> If you are still thinking about it a month later, {{contact.first_name}},
> that is generally your answer.
>
> **So let's get your session on the books.** Pick a time that suits you and
> we will talk the whole thing through — the date, the Collections, the
> payment plan, all of it. You can book as far out as 15 months, so we can
> put your date wherever it suits you and spread the plan across the months
> in between.
>
> **[Book my call →]**
>
> I would love to welcome you into the studio. 🖤
>
> — Jess

**Text:**

> {{contact.first_name}}, it's been 30 days — and I haven't forgotten about
> you!
>
> Women rarely book because of a birthday. They book because they got tired
> of waiting to feel ready. If you are still thinking about it a month
> later, that is generally your answer.
>
> I would love to welcome you into the studio. Let's get your call booked
> and your session on the calendar: [calendar]
>
> — Jess

---

## 7 · 3 months

**Subject:** Three months on — what can I answer for you?

> Hi {{contact.first_name}}!
>
> It has been three months since you reached out about a session with us,
> and I wanted to check in. **What questions can I answer for you?**
>
> In case it helps to see it again, here is what your experience includes:
>
> - ✨ A two to three hour experience in our luxury studio
> - ✨ Professional hair and makeup at a local salon before you arrive (hellooooo makeover!)
> - ✨ Full access to the studio wardrobe — 160 pieces, sizes XS to 4X
> - ✨ A full session where I pose you from head to pointed toe
> - ✨ Expert posing and expression guidance
> - ✨ Retouching, and your private image reveal and ordering appointment
>
> And you never pay for it all at once. Every Collection is bought on an
> **interest-free prepayment plan** — weekly, biweekly or monthly, set up
> within 7 days of booking, with your first payment due within 30 days. You
> can book your session **up to 15 months in advance**, too, so your plan
> spreads across as many payments as you need to keep the amount manageable.
>
> You have been thinking about this for three months, {{contact.first_name}}.
> Let's do it!
>
> **[Book my call →]** — no obligation, just a conversation.
>
> — Jess

**Text:**

> {{contact.first_name}}, three months since you reached out! What questions
> can I answer for you?
>
> Your experience includes the studio, hair and makeup at a local salon
> beforehand, the full wardrobe — 160 pieces, XS to 4X — your session with
> me posing you head to pointed toe, retouching, and your private image
> reveal and ordering appointment.
>
> And you never pay for it all at once. Every Collection is on an
> interest-free prepayment plan — weekly, biweekly or monthly. You can book
> up to 15 months out, so the amount stays manageable.
>
> You have thought about it. Let's do it! Book a no-obligation call:
> [calendar]
>
> — Jess

---

## 8 · 6 months

**Subject:** My door is always open 🖤

> Hi {{contact.first_name}},
>
> This is the last time I will reach out, so I wanted to make it count.
>
> Thank you for thinking of my studio in the first place. With everywhere
> you could have looked, that still means a great deal to me.
>
> **My door is always open to you.** Next month, next year, whenever the
> time is right — I would love to have you in.
>
> **[Book my call →]**
>
> You are worth it, {{contact.first_name}}. Truly. And I would be honored to
> be the one who captures you.
>
> — Jess

**Text:**

> {{contact.first_name}}, this is my last message — but my door is always
> open.
>
> Thank you for thinking of my studio in the first place. With everywhere
> you could have looked, that means a great deal to me.
>
> Next month, next year, whenever the time is right — I would love to have
> you in. You are worth it, and I would be honored to be the one who
> captures you.
>
> [calendar] — Jess

---

## Notes on the writing

**The voice is hers, lifted from her own inquiry email and then corrected by
her line by line.** "I'm so excited you reached out", "hellooooo makeover",
"totally normal, everyone is", "nervous turns into empowered real quick",
"you'll leave feeling like a damn goddess", "got a little sticker shock?
totally get it", "that's literally my job", "you've thought about it, let's
do it", "I'd be honored to capture you."

**Each message has one job.** Welcome, reassure, name the fear, explain the
day, talk money, ask for the booking, touch base, and finally close the door
gently. Her Dubsado version sent one message six times; this is the same
cadence doing eight different things.

**Every message now ends on the calendar.** That was her steer on the later
touches and it is right: a nurture sequence that explains beautifully and
never asks is just a newsletter. Messages 5, 6, 7 and 8 ask directly.

**All eight texts are live.** An earlier draft marked three optional on the
grounds that eight in six months might be a lot; she wrote copy for every one
of them, which settles it.

**Each text now carries its email's argument, not just its link.** Her steer
on 25 September: *"I want these emails and texts to resemble the dubsado
workflow emails. Create the texts based on what the email says."* So the
72-hour text makes the nervousness case and asks for the phone call, the
7-day text walks the day, the 14-day text names the investment, and so on.
They are shorter than the emails and say the same thing.

**The 15-month booking window is now an affordability argument, not a
logistics detail.** Her steer: a woman who can book that far out spreads her
prepayment plan across that many more payments, which is what makes the
amount manageable for most. So it appears in the three money messages -- 5
and 7 beside the plan terms, and 6 where the call already promises to cover
the date and the plan together -- and nowhere else. **Not** in messages 1 to
4, which quote no figures on purpose, and not in message 8, which is a
goodbye and would read as a last pitch. The number matches the FAQ and the
Session Guide; 15 months is the settled figure and her old Dubsado copy's
18 months is the stale one.

**No emoji in any text.** Her instruction, and it is the right one for SMS:
a heart renders differently on every handset and some carriers still turn a
text with emoji into an MMS, which costs more and can silently fail. The
emails keep theirs.

**The thank-you is in message 1 and message 8 and nowhere between.** Her
note: *"there are many choices for a boudoir photographer and I appreciate
them choosing to inquire with my studio."* In all eight it stops reading as
gratitude and starts reading as a tic.

**Message 3 is the one that stays steady.** Everything else carries her
energy and exclamation marks. Three is answering a woman who thinks she is
not good enough to be photographed, and brightness there would read as not
listening. Message 8 used to be quiet too; she has turned it into a warm
final ask, which is a better instinct — a goodbye that still believes in the
woman reading it.

**The reviews are real.** Message 3 uses Miss H., unplaced on the site — see
`reviews.md`. Message 6 uses two lines from the Portfolio and The Experience.
The one-review-one-page rule in `CLAUDE.md` is about the website; re-using
them in email is fine and worth knowing rather than discovering.

**What is deliberately not here:** a discount, an artificial deadline, and a
"spots are filling up". She runs none of those, and manufacturing urgency for
a woman deciding whether to be photographed in her underwear is the wrong
instinct. (The 7-day plan deadline is a real term of business, not a pressure
tactic.)

---

## One thing left: the payment terms belong on the site

Message 5 and message 7 both state that a plan is **set up within 7 days of
booking, with the first payment due within 30 days**. The website does not
say this anywhere.

A term of business that lives in an email and nowhere else is the drift this
project keeps finding — the Canva guide, her Dubsado emails, and now this.
`CLAUDE.md` is explicit that **every figure lives in the FAQ**.

The FAQ's payment answer currently reads:

> Yes, and every collection is bought through one. You set yours up when you
> book, and pay weekly, biweekly or monthly — whichever suits you.
>
> They are interest free. It is the same figure either way, spread out. You
> may book your session up to 15 months in advance.

**Proposed, for her approval** — one sentence changed, nothing removed:

> Yes, and every collection is bought through one. You set yours up **within
> seven days of booking** and pay weekly, biweekly or monthly — whichever
> suits you. **Your first payment is due within thirty days.**
>
> They are interest free. It is the same figure either way, spread out. You
> may book your session up to 15 months in advance.

One generator, one template patch, one page render. **Not done** — a payment
deadline on a live client-facing page is hers to approve.

**And post-payment plans are now nowhere at all.** Klarna, Affirm, AfterPay
and PayPal Credit are still offered — she confirmed that on 25 September —
but she then had them taken out of message 5, and they have never been on the
site. So a woman who could only say yes with Klarna currently has no way to
find out that she can. Worth a line in that same FAQ answer if she wants it;
worth nothing at all if she would rather not lead with it.
