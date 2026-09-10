clone the repo:
---------------------------
cd Desktop
git clone https://github.com/Omarr127/Software_Tesitng_Agent.git
cd Software_Tesitng_Agent
------------------------------


- For API key:
 ------------
set GEMINI_API_KEY=YOUR_API_KEY
------------

-Scenarios test:
scenario 1 input:
py main.py --requirement "Test the search functionality on the application by searching for centrifuge and verify that the correct search results are displayed." --app_path "http://127.0.0.1:5050"


scenario 2 input:
py main.py --existing_script "agent-browser open http://127.0.0.1:5050\nagent-browser mouse move 430 260\nagent-browser mouse down left\nagent-browser mouse up left\nagent-browser press Control+a\nagent-browser clipboard write \"centrifuge\"\nagent-browser clipboard paste\nagent-browser mouse move 1010 260\nagent-browser mouse down left\nagent-browser mouse up left" --app_path "http://127.0.0.1:5050"


scenario 3 input:
py main.py --app_path "http://127.0.0.1:5050"
