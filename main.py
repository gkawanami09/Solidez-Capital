from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = 'chave_secreta_solidez'

usuarios = []
transacoes_db = []
investimentos_db = []


@app.context_processor
def inject_vars():
    return{
        'now': datetime.now(),
        'datetime': datetime
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'usuario_logado' in session:
        return redirect(url_for('painel'))



    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        usuario = next((u for u in usuarios if u['email'] == email), None)
        if usuario and check_password_hash(usuario['senha'],senha ):
            session['usuario_logado'] = usuario['email']
            session['nome_usuario'] = usuario['nome']
            session['saldo'] = usuario.get('saldo',0)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('painel'))
        else:
            flash('Email ou senha incorretos!', 'danger')

    return render_template('login.html')


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        cpf = request.form['cpf']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']

        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'danger')

        if any(u['email'] == email for u in usuarios):
            flash('Email já cadastrado!' , 'danger')
            return redirect(url_for('cadastro'))

        if any(u.get['cpf'] == cpf for u in usuarios):
            flash('CPF já cadastrado!' , 'danger')
            return redirect(url_for('cadastro'))

        usuarios.append({
            'nome': nome,
            'email': email,
            'senha': generate_password_hash(senha),
            'saldo': 0,
            'investido': 0

        })

        flash('Cadastro realizado com sucesso!Faça o Login', 'success')
        return redirect('login.html')

    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    session.pop('nome_usuario', None)
    session.pop('saldo', None)
    flash('Você foi deslogado com sucesso!' , 'info')
    return redirect(url_for('index'))



@app.route('/editar', methods=['GET', 'POST'])
def editar_usuario():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    usuario = next((u for u in usuarios if u['email'] == session['usuario_logado']), None)

    if not usuario:
        flash("Usuário não encontrado!" , 'danger')
        return redirect(url_for('painel'))

    if request.method == 'POST':
        usuario['nome'] = request.form['nome']
        novo_email = request.form['email']
        novo_cpf = request.form.get['cpf']

        if novo_email != usuario['email'] and any(u['email'] == novo_email for u in usuarios):
            flash("Este email já está em uso por outro usuário", 'danger')
            return redirect(url_for('editar'))

        if 'cpf' in request.form and novo_cpf != usuario.get('cpf', '') and any(u.get('cpf') == novo_cpf for u in usuarios):
            flash("Este CPF já está sendo usado", 'danger')


        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')

        if senha_atual or nova_senha or confirmar_senha:
            if not check_password_hash(usuario['senha'], senha_atual):
                flash("Senha atual incorreta",  'danger')
                return redirect(url_for('editar'))

        if nova_senha != confirmar_senha:
            flash('Nova senha e confirmação de senha não coincidem' , 'danger')
            return redirect(url_for('editar'))
        if len(nova_senha) < 8 or len(nova_senha) > 12:
            flash("A nova senha deve ter no minímo 8 caracteres e máximo 12 caracteres")
            return redirect(url_for('editar'))


        usuario['email'] = novo_email
        if 'cpf' in request.form:
            usuario['cpf'] = novo_cpf

        session['nome_usuario'] = usuario['nome']
        session['usuario_logado'] = usuario['email']

        flash('Perfil atualizado com sucesso!' , 'success')
        return redirect(url_for('painel'))
    return render_template('ediatr.html', usuario=usuario)


