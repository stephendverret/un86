# UN86 weekly marketing run

Every Thursday a scheduled Claude run makes the next week's Instagram posts, schedules them in Buffer
and messages Stephen a preview. They post unless he says stop.

## Cadence
- 3 posts a week: Monday, Wednesday and Friday at 6:30 PM Central.
- Usually 2 images and 1 reel. The reel goes on Monday or Wednesday.
- Rotate the pillars so no two in a row match: 86 stories (the pain of running out), How it works (one feature at a time),
  Behind the build (built behind a real bar, by restaurant people), Offer (soft open special through Jan 31, 2027; after that the 14-day free trial),
  Free guide (un86.app/foh-order-guide). An offer post at most every other week.
- Read `log.json` first and do not repeat a headline or angle from the last 6 weeks.

## Voice and rules
- Plain, warm, restaurant-floor talk. Short sentences. Sentence case.
- **No French words, phrases, names or ideas, ever.** Avoid Cajun or French surnames in examples (use names like Jordan, Dana, Sam).
- **No location line** (do not say Lafayette or Louisiana) and **no personal names** of the founder on public posts.
- **Do not promise what the app does not do.** It counts, shows what is below par, builds each rep's order for text, email,
  call or their website, tracks deliveries and reports. It does not predict, auto-order or guarantee you never run out.
  Never say "before anyone notices" or similar.
- Facts to keep straight: 14-day free trial, no card. Plans: Meat & Potatoes, The Whole Enchilada, Family Style.
  Invoice scan is on The Whole Enchilada and Family Style. Soft open special: free setup and 50% off the first 3 months,
  first 10 restaurants, through January 31, 2027 (un86.app/softopen). Demo: demo.un86.app (or "the demo at un86.app").
- Captions: hook line, 2 to 4 short paragraphs, one call to action (demo, link in bio, or the guide), 3 to 5 hashtags from:
  #restaurantowner #restaurantlife #barmanager #foh #restaurantmanagement #foodcost #inventory #smallbusiness #bartender
- Reels post without music. Captions on screen carry them.

## Using what's already planned
- The Marketing app may already hold drafts for next week's dates (written before this run existed). Use their headline
  and caption when they still fit, and rebuild the image with make.py (old app images are private, not public URLs).
- Make one post each week a reel even if the drafts are all images: turn the best how-it-works draft into a reel using
  the b-roll clips in kit/broll (count = counting on the phone, order = an order ready to send, ways = vendors by text,
  email, call and website).

## Making the posts
1. `pip install playwright` is already present in the container; run `python3 kit/make.py week.json`
   (see the docstring at the top of make.py for the JSON shape). Look at every image and at frames of every reel before scheduling.
2. Commit the files in `posts/` and push to `main`.
3. Media URLs: `https://raw.githubusercontent.com/stephendverret/un86/main/posts/<file>`. Check each URL returns 200 before scheduling.

## Scheduling in Buffer
- Organization `6b04c5eecddb1bac75435780` ("My organization"), Instagram channel `6b04d0658541f09ecb7fd11e` (@un86.app, business).
- `create_post` with `schedulingType: "automatic"`, `mode: "customScheduled"`, `dueAt` like `2026-12-07T18:30:00-06:00`.
- Images: `metadata.instagram = {type: "post", shouldShareToFeed: true}`, asset `{image: {url, metadata: {altText}}}`.
- Reels: `metadata.instagram = {type: "reel", shouldShareToFeed: true}`, asset `{video: {url}}`.
- Free plan holds 10 scheduled posts at a time.

## Marketing app (Claude artifact 531e82ae-dcf2-418a-a918-19a4cb5dab1b)
- Write each post to `posts/<date>` with fields: date, pillar, title, caption, image, status "scheduled".
  Upload the image with upload_asset first and use its `/_blob/...` url (for reels, upload the cover .jpg).
- Read `ideas` (unused ideas from Stephen) and approved quotes (`leads` with quoteOk true) and use them first.
  Mark an idea used once a post is built from it.

## After scheduling
- Append each post to `log.json` (date, pillar, type, headline, file, bufferPostId) and push.
- Message Stephen a short preview: each day, the headline, the image or reel, and the caption. Say they post unless he says stop.
