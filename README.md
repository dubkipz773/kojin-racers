# Kojin Racers

Working files for the Kojin Racers Shopify store (https://kojinracers.myshopify.com): designs, print files, ad creative, mechanic-service materials, and the ShopLead app.

## What is live vs. what is here

The **live storefront is hosted by Shopify**. The theme that customers see lives in Shopify admin (Online Store → Themes → the published theme). Nothing in this repo is deployed automatically.

Files in this repo are working copies and history, not the source of truth:

| Path | What it is |
| --- | --- |
| `kojin/live/` | Snapshots of live pages (homepage, product pages, policies) taken Nov 11, 2026 |
| `kojin/shipping.html`, `kojin/refund.html` | Policy text that was pasted into Shopify admin on Nov 11, 2026 |
| `kojin-drop*.liquid`, `footer-fixed.liquid`, `*.json` at the root | Older homepage/theme section drafts. **Not deployed**; the live versions are in Shopify admin |
| `backups/` | Timestamped copies of theme files before edits |
| `kojin-print-files/`, `kojin-user-designs/`, `kojin/designs/` | Tee artwork and print-ready files (Printful) |
| `kojin-mockups/`, `kojin-canva-exports/` | Product mockups and Canva exports |
| `kojin-ads/`, `kojin-instagram/`, `kojin-drop02/` | Ad plans, ad creative, social content |
| `kojin-mechanic/` | Mobile mechanic service materials |
| `shoplead/` | ShopLead AI lead-triage app (separate project) |

## Fulfillment

- Tees: printed on demand by Printful.
- Garage gear: CJ Dropshipping.

## Making changes

Edit the theme, products, and policies in Shopify admin. If you change a theme file, save a copy into `backups/` with the date so the history stays in this repo.
