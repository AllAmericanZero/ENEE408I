import logging

from flask import Flask, render_template

from flask_ask import Ask, statement, question, session


app = Flask(__name__)

ask = Ask(app, "/")

logging.getLogger("flask_ask").setLevel(logging.DEBUG)

hinumber=0


@ask.launch
def startup():
    welcome_msg = render_template('welcome')
    return question(welcome_msg)


@ask.intent("follow")
def follow():
    msg = render_template('hi')
    return statement(msg)

@ask.intent("stopfollow")
def stopfollow():
    msg = render_template('hi')
    return statement(msg)



if __name__ == '__main__':
    app.run(debug=True)
