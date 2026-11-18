# worked example (fictional)

this walks through the bundled demo. everything in it is invented: the company, the ad
ids, the orders and the numbers. it exists so you can see the output shape before you
have data of your own.

run it:

```bash
python3 scripts/marketing_os.py init --workspace /absolute/path/to/demo-workspace
python3 scripts/marketing_os.py demo --workspace /absolute/path/to/demo-workspace
```

## the fictional setup

a one-person bookkeeping business sells twelve months of catch-up bookkeeping for 240 EUR
once, with a full refund if the year cannot be caught up. thirty-one collected quotes give
a promise in the buyer's own words: "you will know what you owe before the deadline, not
after it".

three ads differ in one thing only, the opening line: the surprise bill, the shoebox of
receipts, the deadline date. the headline, description, image style, page and audience are
identical. the page headline repeats the ad headline almost word for word.

the owner sets a 900 EUR cap for the whole test, an end date two weeks out, a fourteen day
wait before any verdict, and a written rule for what would count as a clear answer. the
agent sets none of those.

## the supplied data

two csv files, both labelled fictional. they deliberately contain the problems real
exports contain: one duplicated ad row, one ad row with a non-numeric spend, one duplicated
order, one order with a non-numeric amount, one sale with no ad id at all, one refund and
one repeat purchase.

## what the reading says

platform reported, over 2027-02-01 to 2027-02-14, one account, one currency:

| ad | spend | platform results | cost per platform result |
|---|---|---|---|
| a_demo_1001 surprise-bill | 412.50 EUR | 14 | 29.46 EUR |
| a_demo_1002 shoebox | 408.00 EUR | 19 | 21.47 EUR |
| a_demo_1003 deadline | 22.40 EUR | 0 | not observed |

sales records, counting only orders that carry an ad id:

| ad | linked new paying | cost per new paying customer |
|---|---|---|
| a_demo_1001 | 2 | 206.25 EUR |
| a_demo_1002 | 1 | 408.00 EUR |
| a_demo_1003 | 0 | no observed cost per customer yet |

the arithmetic is exact decimal division, shown in the output: 412.50 / 2 = 206.25, and
408.00 / 1 = 408.00. the third ad is not divided at all, because dividing by zero
customers would produce a number that means nothing.

## what it refuses to say

- the shoebox ad is the cheapest per platform result. the surprise-bill ad is the cheapest
  per customer who actually paid. those are different ads, and the reading says so instead
  of picking the comfortable one.
- the third ad took about three percent of the window's spend. the output reports that
  share as a description, not as a threshold, and gives no verdict on the ad.
- the platform counted 33 results while the sales records link 3 new paying customers.
  both can be honest. they are never added together.
- one refund, one repeat purchase and one sale of unknown origin are each on their own
  line. none of them is quietly folded into a win.
- only two days have passed since the window ended, against a fourteen day wait, so the
  verdict is **NOT MATURE** and nothing is paused or scaled.

## what happens next

`next-work-and-learning` writes two proposals: a "we do not know yet" note, because the
two leaders disagree and the data is immature, and a fact problem if any quote contradicts
the brief. no learning is recorded, because nothing earned one. the next job is to read the
same test again after the wait period.

that is the deliverable of this system. a smaller answer you can defend.
