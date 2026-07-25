# buydecide-feed-lab

Synthetic product-feed fixtures for the BuyDecide connector lab
(technical acceptance for scheduled-pull + conditional-poll connectors).
Contains NO merchant data: product facts with deterministically jittered
prices. `feeds/feed-c.json` is re-jittered daily by the scheduled Action;
the other two files are static on purpose (their polls exercise real
HTTP 304 behavior).
