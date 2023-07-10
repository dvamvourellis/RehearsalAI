# RehearsalAI

LLM application for creating hypothetical debates between two [(CAMEL)](https://www.camel-ai.org/) agents. 
You can use the app to rehearse a conversation you are interested in between two given roles (e.g. negotiate with your manager, rehearse an ucomfortable discussion with your mom etc.).
The app can help you find potentially useful arguments and how these might be challenged from the other side.

You can access the application [(here)](https://rehearsal-ai.streamlit.app/).

To use the app, pleae input;
- A valid OpenAI API key.
- Two roles (e.g. employee and manager)
- Topic of debate (e.g. raise salary)
- How many turns the dialogue should last for

Optionally you can also input:
- A few characteristics about each role in a comma separated list (e.g. funny, arrogant etc.)
- A few points that should be used as the argumen tbasis for role 1 (e.g. employe if you enter this as role 1)
- A minimum outcome you would like role 1 to have after discussion. In this way you can force role 1 to provide an alternative if he cannot persuade role 2.
