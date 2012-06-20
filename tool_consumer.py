from flask import Flask, render_template, session, request, redirect, url_for

app = Flask(__name__)
app.secret_key = '\xb9\xf8\x82\xa9\xf4\xdcC\xf4L<\x9c\xf1\x87\xa6\x7fI\xb9\x04\x9d\xed\xb0\xf2\x83\x0c'

@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html')

@app.route('/set_name', methods = ['POST'])
def set_name():
    session['username'] = request.form['username']
    return redirect(url_for('tool_config'))

@app.route('/tool_config')
def tool_config():
    if not session.get('username'):
        return redirect(url_for('index'))

    return render_template('tool_config.html',
            message = request.form.get('message'),
            username = session['username'])

if __name__ == '__main__':
    app.run()
