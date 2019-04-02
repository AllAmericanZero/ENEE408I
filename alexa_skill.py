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


@ask.intent("hi")
def hi():
    hinumber += 1
    msg = render_template('hi', number=hinumber)
    return statement(msg)


@ask.intent("addthree", convert={'first': int, 'second': int, 'third': int})
def answer(first, second, third):
    result = first+second+third
    msg = render_template('addthree',number = result)
    return statement(msg)


if __name__ == '__main__':
    app.run(debug=True)
