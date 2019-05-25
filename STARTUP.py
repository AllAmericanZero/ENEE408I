import webbrowser
import os

webbrowser.open('https://developer.amazon.com/alexa/console/ask/build/custom/amzn1.ask.skill.c3bd6ed2-4cb7-49a7-83e7-9cca21a126cb/development/en_US/endpoint', new = 2)

os.system("ngrok.exe http 5000")
os.system("python alexa_skill.py")
os.system("python movement_controller.py")
