# business brief

Status: DRAFT

this file is the one place the whole system reads from. every ad, page, post and
reading has to agree with what is written here. write MISSING for anything you do
not know yet. never guess, and never let a draft fill one of these lines for you.

the owner changes the status line to `Approved by owner on YYYY-MM-DD` only after
reading every line below.

## machine fields

these lines are read by `marketing_os.py doctor`. keep the `- key: value` shape.

- status: DRAFT
- offer_name: MISSING
- what_the_buyer_gets: MISSING
- price_and_terms: MISSING
- guarantee_exact_wording: MISSING
- primary_action: MISSING
- where_they_act: MISSING
- buyer_in_one_sentence: MISSING
- not_for: MISSING
- usual_days_to_purchase: MISSING
- claims_we_must_never_make: MISSING
- existing_assets: MISSING
- tools_we_build_in: MISSING
- ad_platform: MISSING
- ad_account_name: MISSING
- ad_account_id: MISSING
- currency: MISSING
- timezone: MISSING
- sales_system_id: MISSING
- ad_to_sale_link: MISSING
- attribution_window_used_in_reports: MISSING
- approved_message: MISSING

## notes on the harder fields

`usual_days_to_purchase` decides when a reading is allowed to be called. if buyers
usually think for two weeks, a quiet first week is not a failed ad.

`claims_we_must_never_make` is the line that protects you. anything you cannot
prove goes here, and no draft is allowed to say it.

`ad_to_sale_link` is how a sale gets traced back to one ad: a link tag that carries
the ad id into the sales record, a code per ad version, or a form field. if this says
`not set up`, cost per customer cannot be computed and the system will say so instead
of inventing a number.

`sales_system_id` is the name of the system that records money arriving. it is not the
ad account id and it does not have to match it.

no passwords, keys, tokens or login links in this file. names and ids only.
