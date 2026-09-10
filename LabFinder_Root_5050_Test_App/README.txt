LABFINDER - SINGLE URL TEST APP

Install:
    py -m pip install flask

Run:
    py app.py

ONLY APPLICATION URL:
    http://127.0.0.1:5050

There is no /labfinder path and no other application page.

Recommended Agent Browser S1 test:
    py main.py --requirement "Search for centrifuge and verify that the results contain laboratory centrifuge equipment and do not select the irrelevant trending consumer items." --app_path "http://127.0.0.1:5050"

Expected centrifuge results:
- Benchtop Centrifuge
- High-Speed Centrifuge
- Mini Microcentrifuge

The Trending Now products are intentional distractors.
