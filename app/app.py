from flask import Flask, render_template
from app import create_app
import time


app = create_app()


@app.route('/')
def hello_world():
    return render_template('Echarts.html')


@app.route('/time')
def get_time():
    return get_time()

def get_time():
    str_time = time.strftime("%Y{}%m{}%d{}%X")
    return str_time.format("年","月","日")

if __name__ == '__main__':
    app.run()
