from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'chave_financeira_segura'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/transacoes')
def transacoes():
    return render_template('transacoes.html')


@app.route('/painel')
def painel():
    return render_template('painel.html')


@app.route('/investimentos')
def investimentos():
    return render_template('investimentos.html')


@app.route('/emergencia')
def emergencia():
    return render_template('emergencia.html')


@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')


@app.route('/login')
def login():
    return render_template('login.html')









if __name__ == '__main__':
    app.run(debug=True)

