# Dostavista Business API — TODO / Progress

- [x] Scaffold project folder and structure (`dostavista/`)
- [x] OpenAPI 3.1.0 skeleton with servers and security (X-DV-Auth-Token)
- [x] Orders: calculate, create, list, edit, cancel
- [x] Receipts: order cost breakdown (GET /receipts)
- [x] Intervals: delivery intervals (GET /delivery-intervals)
- [x] Deliveries: create/edit/delete/list drafts + make routes
- [x] Couriers: data and location by `order_id`
- [x] Client: profile and allowed payment methods
- [x] Bank cards: attached cards list
- [x] Lint and validate (Redocly + Swagger CLI)
- [x] Add initial LLM examples for implemented endpoints
- [ ] Expand models (Order, Point, Package, Delivery, etc.) with all fields from donor HTML
  - [x] Add lengths and validation (matter, backpayment_details, address, client_order_id, loaders_count)
  - [x] Add missing point input fields (arrival_courier_note, delivery_id)
  - [x] Tighten package field constraints (ware_code, description, item_payment_amount)
- [ ] Add all donor CURL and response examples per endpoint (postpone to final stage)
- [x] Add common error codes and parameter error codes as `components/schemas` and reference in responses
- [ ] Optional: generate TS types via `openapi-typescript` (commit only if types tracked)
- [ ] Optional: local mock via Prism for spot checks
- [x] Optional: dictionaries (if applicable in donor docs)
\- [ ] At the end: add examples to all endpoints (from donor) if time allows
