from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = 'chave_secreta_solidez'

usuarios = []
transacoes_db = []
investimentos_db = []


@app.context_processor
def inject_vars():
    return {
        'now': datetime.now(),
        'datetime': datetime
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        usuario = next((u for u in usuarios if u['email'] == email), None)

        if (usuario and (usuario['senha'] == senha)):
            session['usuario_logado'] = usuario['email']
            session['nome_usuario'] = usuario['nome']
            session['saldo'] = usuario.get('saldo', 0)

            flash('Login realizado com sucesso!', 'success')
            return redirect('/painel')
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
        confirmar_senha = request.form['senhaa']

        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'danger')
            return redirect(url_for('cadastro'))

        if any(u['email'] == email for u in usuarios):
            flash('Email já cadastrado!', 'danger')
            return redirect(url_for('cadastro'))


        if any(u.get('cpf') == cpf for u in usuarios):
            flash('CPF já cadastrado!', 'danger')
            return redirect(url_for('cadastro'))

        usuario = {
                'nome': nome,
                'email': email,
                'cpf': cpf,

                 'senha': senha,
                 'saldo': 0,
                 'investido': 0
                }
        usuarios.append(usuario)

        flash('Cadastro realizado com sucesso! Faça login.', 'success')

        return render_template('login.html')

    return render_template('cadastro.html')


@app.route('/painel')
def painel():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    usuario = next((u for u in usuarios if u['email'] == session['usuario_logado']), None)
    usuario_transacoes = [t for t in transacoes_db if t['usuario'] == session['usuario_logado']][
                         -5:]

    return render_template('painel.html',
                           saldo=session['saldo'],
                           investido=usuario['investido'] if usuario else 0,
                           transacoes=usuario_transacoes)
@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    session.pop('nome_usuario', None)
    session.pop('saldo', None)
    flash('Você foi deslogado com sucesso!', 'info')
    return redirect(url_for('index'))


@app.route('/usuario/editar', methods=['GET', 'POST'])
def editar_usuario():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    usuario = next((u for u in usuarios if u['email'] == session['usuario_logado']), None)
    if not usuario:
        flash("Usuário não encontrado!", 'danger')
        return redirect(url_for('painel'))

    if request.method == 'POST':
        usuario['nome'] = request.form.get('nome', usuario['nome'])
        novo_email = request.form.get('email', usuario['email'])

        # Verificação de email existente
        if novo_email != usuario['email'] and any(u['email'] == novo_email for u in usuarios):
            flash("Este email já está em uso!", 'danger')
            return redirect(url_for('editar_usuario'))

        usuario['email'] = novo_email

        # Atualização de CPF
        novo_cpf = request.form.get('cpf')
        if novo_cpf and novo_cpf != usuario.get('cpf'):
            if any(u.get('cpf') == novo_cpf for u in usuarios):
                flash("CPF já cadastrado!", 'danger')
                return redirect(url_for('editar_usuario'))
            usuario['cpf'] = novo_cpf

        # Atualização de senha
        nova_senha = request.form.get('nova_senha')
        if nova_senha:
            if nova_senha != request.form.get('confirmar_senha'):
                flash("As senhas não coincidem!", 'danger')
                return redirect(url_for('editar_usuario'))
            if len(nova_senha) < 8:
                flash("A senha deve ter no mínimo 8 caracteres!", 'danger')
                return redirect(url_for('editar_usuario'))
            usuario['senha'] = nova_senha

        # Atualizar sessão
        session['usuario_logado'] = usuario['email']
        session['nome_usuario'] = usuario['nome']

        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('visualizar_usuario'))

    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/usuario')
def visualizar_usuario():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    usuario = next((u for u in usuarios if u['email'] == session['usuario_logado']), None)
    if not usuario:
        flash("Usuário não encontrado!", 'danger')
        return redirect(url_for('painel'))

    usuario_exibicao = {k: v for k, v in usuario.items() if k != 'senha'}
    return render_template('visualizar_usuario.html', usuario=usuario_exibicao)


if __name__ == '__main__':
    app.run(debug=True)