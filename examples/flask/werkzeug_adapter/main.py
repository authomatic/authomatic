# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, make_response
from authomatic.adapters import WerkzeugAdapter
import authomatic

from config import CONFIG

app = Flask(__name__)

authomatic.setup(CONFIG, '123')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login/<provider_name>/', methods=['GET', 'POST'])
def login(provider_name):
    
    response = make_response()
    
    result = authomatic.login(WerkzeugAdapter(request, response), provider_name)
    
    if result:
        if result.user:
            result.user.update()
        
        return render_template('login.html', result=result)
    
    return response

if __name__ == '__main__':
    app.run(debug=True, port=8080)
