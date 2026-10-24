# CCMC checkout: 2027 Charity Calendar Model Call (files only, nothing deployed)

Prepared 2026-10-24. Nothing was written to Scalogy. All reads were read-only (db_query SELECT, db_schema, pages_read, pages_list, apps_list/apps_read, fs_read).
Source checks: the live template `forms-pspp-setup-editorial-pspp-checkout-v2` (47f596b3…) is byte-identical to `raw/tpl__pspp_checkout_v2.html`, because pages_read on both giveaway pages returned the same template_html. Live `scripts/promote_psppv2_inbox.py` (fs_read) is identical to `recon/promote_psppv2_inbox.py`.

## Files in this folder
| File | What |
|---|---|
| template_patches.json | 12 search/replace blocks for `templates_patch` on 47f596b3… (each search matches exactly once, checked one after another) |
| patched_template.html / patched.diff | result of applying them, and the unified diff |
| template_patches_OPTIONAL_book_end_2028.json | NOT part of the main set. Lets CCMC book through Mar 31 2028. See open question 2 |
| server_patches.json / server_patched.diff / patched_promote_psppv2_inbox.py | 2 blocks for scripts/promote_psppv2_inbox.py (py_compile OK) |
| contract_ccmc_DRAFT.md | contract for Jessica's review. Every changed or new line is marked **[CHANGED]** |
| contract_ccmc_CLEAN.md | the same text without markers. This is what gets stored |
| insert_contract_ccmc_2027.sql | ready INSERT built from the CLEAN text. Rebuild it if the text changes (`python3 -I tools/contract.py`) |
| key_acks_ccmc.json | the initialled acknowledgements as the CCMC pages will show them (2-card + 1-card) |
| verification.txt | node run of the original vs patched template JS for 8 paths × 3 `?campaign=` values |
| tools/ | build.py (patches + checks), probe.py + harness.js (behaviour comparison), contract.py |

## Template: every IS_2027 use and what CCMC does
`IS_CCMC = path contains 'forms-pspp-2027-ccmc'`. This flag is separate from IS_2027 and the two paths never overlap.
| Line (orig) | Use | CCMC decision |
|---|---|---|
| 314 | `IS_2027` definition | unchanged. CCMC paths do not contain `lpl-giveaway`, so IS_2027 stays false on CCMC |
| 315 | FORM_VERSION | `IS_CCMC?'2027-ccmc':…` (own value) |
| 316 | SINGLE_CARD | adds `forms-pspp-2027-ccmc-1cc` |
| 330 | LINEUP_2027 (menu) | SHARED: `IS_2027‖IS_CCMC‖!IS_SPECIALTY` (already true via !IS_SPECIALTY; made explicit) |
| 337 | IS_LASTMIN exclusion | SHARED: `&&!IS_CCMC` |
| 662 | document.title | own: '2027 Charity Calendar Model Call — JHP Boudoir' (+ ' (Single Card)' is still appended by the existing code) |
| 1163 ×2 | single/two-card cross links | own: `../forms-pspp-2027-ccmc(-1cc)/` |
| 1420 | form_name | own: '2027 Charity Calendar Model Call' / '… (Single Card)' |

Other places changed for CCMC that IS_2027 does NOT cover today (these make CCMC "never flash"):
- 371 `BOOK_START`: the flash-sale Oct-1 start is ignored on CCMC.
- 608 `IS_FLASH &&!IS_CCMC`: without this, `?campaign=flash-sale` on a CCMC link would swap in the flash contract, hide Petite 3 and show a $1,500 minimum. The giveaway pages do still react to that param today. I left that existing behaviour alone.
- Contract (after line 610): `contract-ccmc-2027` / slug `boudoir-session-contract-charity-calendar-model-call` / title 'Boudoir Session Contract - Charity Calendar Model Call'.
- KEY_ACKS: the giveaway ack (index 4) is replaced by the CCMC program ack, and a calendar-entry ack is spliced in after it. All other acks are the giveaway list verbatim.

Proof that existing pages don't change (verification.txt): the template JS was run under node with a stubbed DOM for forms-pspp-setup-pspp-checkout-v2, -setup-1cc, -2027-lpl-giveaway(-1cc), -setup-specialty and treehouse-pc-investment, each with no query, `?campaign=last-minute` and `?campaign=flash-sale`. The run compared IS_2027, FORM_VERSION, SINGLE_CARD, IS_SPECIALTY, IS_PASTCLIENT, LINEUP_2027, IS_LASTMIN, IS_FLASH, BOOK_START/END, CONTRACT_*, KEY_ACKS, the full COLLECTIONS array (ids, names, prices, contents), WEBHOOK_URL, PSPP_VERSION, PSPP_TERMS, PAYOFF_LEAD, title, form_name and both cross links. All 18 cases are identical, and IS_CCMC is false on every one. By reasoning: every edit either adds a `&&!IS_CCMC` / `‖IS_CCMC` term or puts an `IS_CCMC?…:` branch first, so when IS_CCMC is false each expression reduces to the original.
CCMC vs giveaway, also checked under `?campaign=last-minute` and `?campaign=flash-sale`: the COLLECTIONS menu and prices, booking window, webhook, PSPP agreement, LM and flash flags are all identical. Only these differ: CONTRACT_*, FORM_VERSION, KEY_ACKS, form_name, links and title.
Menu on CCMC: Artist 9,400 · Diamond 6,900 · Gold 5,100 · Full Digital Gallery 4,500 · Silver 2,900 · Petite 15 2,200 · Petite 8 1,500 · Petite 3 750.

## Server (promote_psppv2_inbox.py)
`2027-lpl-giveaway` appears in 2 code places (plus comments at lines 89/93, which need no change):
1. line 383, the last-minute pricing exclusion: now `not in ("2027-lpl-giveaway", "2027-ccmc")`. This is belt-and-braces, since the CCMC page never sends campaign=last-minute.
2. line 1248, the failed_no_cards retry link: a new `elif` sends CCMC clients to forms-pspp-2027-ccmc(-1cc).
CANON_PRICES already covers every id on the 2027 menu, so pricing is the same as the giveaway. Both workflows, promote-psppv2-inbox and promote-psppv2-inbox-1cc, run this same script, so one fs patch covers both.

## Objects to create (in this order, after Jessica approves the contract and acks)
1. **Asset row** `contract-ccmc-2027` in psppv2_form_assets. This mirrors `contract-flash-2026` / `contract-lastminute-2026`: key, label, content_type `text/markdown`, bytes = UTF-8 length, data_b64 = base64 of the UTF-8 text, source_url = provenance note. Run `insert_contract_ccmc_2027.sql` through db_query (49 KB, under the 64 KB limit, no backslashes). First replace `<DATE>` in source_url. Check it with `SELECT key,bytes,length(data_b64) FROM psppv2_form_assets WHERE key='contract-ccmc-2027'` (expect 36779 / 49040 if the text is unchanged). The page fetches this table through _api (limit 200, now 21 rows), so the row needs no re-render. Until the row exists, `contractSrc()` is null and step 3 cannot be completed, so the page fails closed.
   - Optional: add the same text to `jhp_contract_templates` (slug `boudoir-session-contract-charity-calendar-model-call`, title as above, body_md) so the signed-forms viewer can show the text. The last-minute contract has no row there either, so this is not required.
2. **Server fs patch**: apply server_patches.json to `scripts/promote_psppv2_inbox.py` (fs_patch). Do this before the pages go live.
3. **Template patch**: templates_patch 47f596b3… with template_patches.json.
4. **Pages** (pages_create + pages_set_template → 47f596b3…):
   - `forms-pspp-2027-ccmc`, named '2027 Charity Calendar Model Call'. Attach it to app **pspp-checkout-v2** (5db20c87…), the app holding forms-pspp-2027-lpl-giveaway. Its tables: psppv2_form_assets, psppv2_checkout_status, psppv2_promo_preview, ghl_session_slots.
   - `forms-pspp-2027-ccmc-1cc`, named '2027 Charity Calendar Model Call (Single Card)'. Attach it to app **pspp-checkout-1cc** (a9e2286e…), the app holding forms-pspp-2027-lpl-giveaway-1cc. Same 4 tables, plus schedule promote-psppv2-inbox-1cc and webhook pspp-checkout-trigger-1cc.
   - Attach no new tables.
5. **Render**: the template patch changes the shared template, so re-render EVERY page bound to it, or those pages keep serving the old HTML. Their behaviour is unchanged either way. Render list: forms-pspp-2027-ccmc, forms-pspp-2027-ccmc-1cc, forms-pspp-setup-pspp-checkout-v2, forms-pspp-setup-1cc, forms-pspp-2027-lpl-giveaway(-1cc), forms-pspp-setup-specialty, treehouse-pc-investment. If you prefer, render only the two new pages, because the old pages behave identically with or without the patch.
6. Smoke test with `?test=1`: two-card and single-card, menu, contract text, 10 acks, the cross links, and that the inbox row has form_version `2027-ccmc` and form_slug `pspp-setup-2026` / `-1cc`.

## Booked Workflow / enroll-booked-on-pspp
- form_slug stays `pspp-setup-2026` / `pspp-setup-2026-1cc`, because the patches do not touch line 1419.
- The webhooks are the existing pspp-checkout-trigger(-1cc), so promote-psppv2-inbox(-1cc) claims the rows.
- `ops/enroll_booked_on_pspp.py` picks up every completed, non-test psppv2_form_responses row except the specialty and treehouse-pc slugs. CCMC bookings are therefore enrolled in 'Booked Workflow - 07/26' and get the GHL Boudoir Sessions Calendar appointment.
- The runner's `form_completed` gate matches `pspp-setup-2026%`, so step 1 fires.
- The new contract slug only matters to workflows gated on a *specific* contract slug (lpl_giveaway, birthday, fill-calendar). Booked Workflow step 1 is gated on form_completed, so it is unaffected.

## Risks / flags
- **Promo codes stack**: the CCMC page shows the promo-code field (as the giveaway does). A code such as TREEHOUSE500 would come off on top of the built-in $500. Hiding it means adding `IS_CCMC` to the `IS_LASTMIN‖isBnpl()` condition at line 1079, and the server ignores codes only for LM. Ask Jessica.
- **No server-side gate**: anyone with the URL can book the CCMC menu (and the $500-off prices) without having paid the $99. The giveaway pages work the same way, and the 2027 prices are the same as on every non-specialty page since 2026-10-13. The $99 claim page and its charge flow do not exist in Scalogy yet. Only the landing/application page charity-calendar-2027 exists.
- **Public-writable assets table**: psppv2_form_assets is attached with allow_write and is publicly readable (security_check: critical `table_public_write`). Anyone with a page token can change contract text. This is an existing risk that the new contract inherits.
- `?campaign=flash-sale` on the *giveaway* pages still switches to the flash contract. That is unchanged and outside this scope.
- psppAgreeText still says '2026 Pre-Session Payment Plan Agreement' and PSPP_VERSION pspp-2026-jhp…, same as the giveaway.

## Open questions for Jessica
1. **Session window**: the landing page and the charity-calendar-2027 page description say sessions run **Nov 2026 – Oct 2027**, but the brief says Oct 2026 – Oct 2027. The contract draft says only "held through October 2027", so it doesn't commit to a start month.
2. **Through March 2028**: the checkout currently ends at **Dec 16 2027** (BOOK_END), and ghl_session_slots runs only to 2027-12-16. To allow Jan–Mar 2028 you need the optional patch, plus ops/ghl_slots_sync.py BOOK_END ≥ 2028-03-31, plus GHL openings. Also, the contract's "reschedule within 6 months" and PSPP "same calendar year" terms interact with late-2027 dates. The March 2028 rate is not written into the contract (it was not asked for). Should it be?
3. Contract line 38 (price list "discussed verbally … over the phone") is kept verbatim. The flash contract reworded it to "published on the landing page". Which fits CCMC?
4. The "No images will be shared publicly without the Client's written permission" sentence in the new clause and the calendar ack repeats the existing Model Release terms. Keep it or drop it?
5. The new clause refers to "a separate release signed … after the Image Reveal". Does that release form exist (Model Release / a calendar-specific release)? It is not created here.
6. Late-arrival $500 reschedule fee, $250/$500/$750 cancellation fees and the 1 free reschedule are all kept from the giveaway contract verbatim. Confirm they apply to CCMC.
