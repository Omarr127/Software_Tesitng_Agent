# Running the Software Testing Agent


This is clearer because the execution order is now:

1. Clone agent repository  
2. Set API key  
3. Start the application under test  
4. Verify port 5050 is running  
5. Run Scenario 1 / 2 / 3 from another CMD window.

## 1. Clone the Repository

Open CMD and run:

```cmd
cd Desktop

git clone https://github.com/Omarr127/Software_Tesitng_Agent.git

cd Software_Tesitng_Agent


set GEMINI_API_KEY=YOUR_API_KEY

cd /app_path


py main.py --requirement "Test the search functionality on the application by searching for centrifuge and verify that the correct search results are displayed." --app_path "http://127.0.0.1:5050"


py main.py --existing_script "agent-browser open http://127.0.0.1:5050
agent-browser mouse move 430 260
agent-browser mouse down left
agent-browser mouse up left
agent-browser press Control+a
agent-browser clipboard write \"centrifuge\"
agent-browser clipboard paste
agent-browser mouse move 1010 260
agent-browser mouse down left
agent-browser mouse up left" --app_path "http://127.0.0.1:5050"




py main.py --app_path "http://127.0.0.1:5050"
