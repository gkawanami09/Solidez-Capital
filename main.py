from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'chave_secreta_solidez'

# Banco de dados simulado
usuarios = []
transacoes_db = []
investimentos_db = []

# Variáveis globais acessíveis nos templates
# Este decorador @app.context_processor define uma função que injeta variáveis globais nos templates HTML.
# Assim, as variáveis 'now' (data e hora atual) e 'datetime' (módulo completo) estarão disponíveis automaticamente
# em todos os arquivos .html renderizados, sem precisar passá-las manualmente com render_template.
@app.context_processor
def inject_vars(): #vai "injetar" em todos os templates
    return {'now': datetime.now(), 'datetime': datetime}


# Rota inicial
@app.route('/')
def index():
    return render_template('index.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        # Procura na lista "usuarios" o primeiro usuário cujo email seja igual ao email da sessão (usuário logado).
        # A função next() retorna esse usuário, se encontrar.
        # Se não encontrar nenhum, retorna None para evitar erro.
        usuario = next((u for u in usuarios if u['email'] == email and u['senha'] == senha), None)

        # Se o usuário foi encontrado (login válido), os dados são armazenados na sessão para manter o usuário logado.
        # - 'usuario_logado': salva o e-mail do usuário logado.
        # - 'nome_usuario': salva o nome do usuário, usado para exibir saudações personalizadas.
        # - 'saldo': salva o saldo atual, obtido com .get() para evitar erro caso o campo não exista.
        if usuario:
            session['usuario_logado'] = usuario['email']
            session['nome_usuario'] = usuario['nome']
            session['saldo'] = usuario.get('saldo', 0)

            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('painel'))
        else:
            flash('Email ou senha incorretos!', 'danger')

    return render_template('login.html')



# Cadastro
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        cpf = request.form.get('cpf')
        senha = request.form.get('senha').strip()  # Adicionando strip() para remover espaços
        confirmar = request.form.get('confirmar').strip()  # Adicionando strip() para remover espaços

        # maiuscula = False
        # minuscula = False
        # numero = False
        # caracterpcd= False

        # for s in senha:
        #     if s.isupper():
        #         maiuscula = True
        #     if s.islowerw():
        #         minuscula = True
        #     if s.isdigit():
        #         numero= True
        #     if s.isalnum():
        #         caracterpcd = True


        # Verifica se as senhas coincidem
        if senha != confirmar:
            flash('As senhas não coincidem!', 'danger')
            return redirect(url_for('cadastro'))

        # Restante do código permanece o mesmo...
        # Verifica se o email já está cadastrado
        # Verifica se já existe algum usuário com o mesmo e-mail.
        # A função `any()` percorre todos os usuários e retorna True se encontrar um com o mesmo e-mail.
        # Isso impede que dois usuários se cadastrem com o mesmo endereço de e-mail.
        if any(u['email'] == email for u in usuarios):    #mudar
            flash('Email já cadastrado!', 'danger')
            return redirect(url_for('cadastro'))

        # Verifica se o CPF já está cadastrado
        # Verifica se já existe algum usuário com o mesmo CPF.
        # A função `any()` retorna True se pelo menos um usuário na lista `usuarios`
        # tiver o mesmo CPF informado no cadastro. Isso evita duplicidade de dados.
        if any(u['cpf'] == cpf for u in usuarios):
            flash('CPF já cadastrado!', 'danger')
            return redirect(url_for('cadastro'))

        # Validação da força da senha
        if len(senha) < 8 or len(senha) > 12:
            flash('A senha deve ter entre 8 e 12 caracteres.', 'danger')
            return redirect(url_for('cadastro'))

        if not re.search(r'[A-Z]', senha): #re ele vai analisar a senha e verificar se ela tem todos requisitos
            flash('A senha deve conter pelo menos uma letra maiúscula.', 'danger')
            return redirect(url_for('cadastro'))

        if not re.search(r'[a-z]', senha):
            flash('A senha deve conter pelo menos uma letra minúscula.', 'danger')
            return redirect(url_for('cadastro'))

        if not re.search(r'[0-9]', senha):
            flash('A senha deve conter pelo menos um número.', 'danger')
            return redirect(url_for('cadastro'))

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
            flash('A senha deve conter pelo menos um caractere especial.', 'danger')
            return redirect(url_for('cadastro'))

        # Se todas as validações passarem, adiciona o usuário
        usuarios.append({
            'nome': nome,
            'email': email,
            'cpf': cpf,
            'senha': senha,
            'saldo': 0,
            'investido': 0
        })

        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html')


# painel
@app.route('/painel')
def painel():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    # Recupera o email do usuário atualmente logado, armazenado na sessão.
    usuario_email = session['usuario_logado']
    # Busca o dicionário do usuário correspondente na lista de usuários.
    # A função `next()` retorna o primeiro usuário cujo 'email' bate com o email da sessão.
    # Se nenhum for encontrado, retorna `None` para evitar erro.    
    usuario = next((u for u in usuarios if u['email'] == usuario_email), None)

    if not usuario:
        flash("Usuário não encontrado!", 'danger')
        return redirect(url_for('login'))

    # Filtra as transações do usuário
    transacoes = [t for t in transacoes_db if t['usuario'] == usuario_email]

    # Cálculos
    # Calcula o total de entradas somando os valores de todas as transações do tipo 'entrada'.
    total_entrada = sum(t['valor'] for t in transacoes if t['tipo'] == 'entrada')
    # Calcula o total de saídas somando os valores de todas as transações do tipo 'saida'.
    total_saida = sum(t['valor'] for t in transacoes if t['tipo'] == 'saida')
    # Calcula o saldo final subtraindo o total de saídas do total de entradas.
    saldo = total_entrada - total_saida
    # Recupera o valor total investido do usuário.
    # Se a chave 'investido' não existir no dicionário do usuário, retorna 0 como padrão.
    total_investido = usuario.get('investido', 0) 

    # Atualiza saldo na sessão
    session['saldo'] = saldo

    return render_template(
        'painel.html',
        usuario=usuario,  # Adicionei esta linha para passar o usuário para o template
        saldo=saldo,
        total_entrada=total_entrada,
        total_saida=total_saida,
        total_investido=total_investido,  # Corrigi o nome da variável
        transacoes=transacoes[-5:] #-5 foi tulizado para aparecer as ultimas 5 transações
    )
# transacoes
@app.route('/transacoes', methods=['GET', 'POST'])
def transacoes():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    email_usuario = session['usuario_logado']

    transacao_em_edicao = None

    # EDITAR TRANSACAO
    if request.method == 'POST' and 'editar_id' in request.form and not request.form.get('data'):
        editar_id = request.form.get('editar_id')
        for t in transacoes_db:
            if t.get('id') == editar_id and t['usuario'] == email_usuario:
                transacao_em_edicao = t
                break

    # EXCLUIR TRANSACAO
    if request.method == 'POST' and 'excluir_id' in request.form:
        excluir_id = request.form.get('excluir_id')
        # Percorre a lista de transações usando enumerate, que retorna tanto o índice (i) quanto o item (t) da lista.
        # Isso é necessário porque vamos precisar do índice para excluir a transação da lista.
        for i, t in enumerate(transacoes_db):
            # Verifica se a transação atual (t) tem o mesmo ID recebido pelo formulário (excluir_id)
            # e se pertence ao usuário logado (comparando o e-mail).
            if t.get('id') == excluir_id and t['usuario'] == email_usuario:
                # Se for a transação correta, usa o índice (i) para removê-la da lista com 'del'.
                # Isso garante que só a transação específica daquele usuário será excluída.
                del transacoes_db[i]
                flash('Transação excluída com sucesso!', 'success')
                return redirect(url_for('transacoes'))

    # SALVAR/ATUALIZAR TRANSACAO
    if request.method == 'POST' and request.form.get('data'):
        data = request.form.get('data')
        descricao = request.form.get('descricao')
        tipo = request.form.get('tipo')
        valor = float(request.form.get('valor', 0))

        if tipo not in ['entrada', 'saida'] or valor <= 0:
            flash('Tipo de transação inválido ou valor não positivo.', 'danger')
            return redirect(url_for('transacoes'))

        editar_id = request.form.get('editar_id')
        if editar_id:
            for t in transacoes_db:
                if t.get('id') == editar_id and t['usuario'] == email_usuario:
                    t['data'] = data
                    t['descricao'] = descricao
                    t['tipo'] = tipo
                    t['valor'] = valor
                    flash('Transação atualizada com sucesso!', 'success')
                    return redirect(url_for('transacoes'))
        else:
            # Importa a função uuid4 do módulo uuid, que serve para gerar identificadores únicos.
            # Isso é útil para garantir que cada transação tenha um "RG" próprio, ou seja, um ID que nunca se repete.
            from uuid import uuid4
            # Adiciona uma nova transação à lista 'transacoes_db'.
            # O campo 'id' recebe um identificador único gerado com uuid4() e convertido para string com str().
            # Esse ID será usado para poder editar ou excluir essa transação depois, sem risco de confundir com outra.
            transacoes_db.append({
                'id': str(uuid4()),   # ID exclusivo para identificar a transação
                'usuario': email_usuario,
                'data': data,
                'descricao': descricao,
                'tipo': tipo,
                'valor': valor
            })
            flash('Transação registrada com sucesso!', 'success')
            return redirect(url_for('transacoes'))

    transacoes_usuario = [t for t in transacoes_db if t['usuario'] == email_usuario]
    return render_template('transacoes.html', transacoes=transacoes_usuario, transacao_em_edicao=transacao_em_edicao)


# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi deslogado com sucesso!', 'info')
    return redirect(url_for('index'))

# Editar perfil
@app.route('/usuario/editar', methods=['GET', 'POST'])
def editar_usuario():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))
    
    # A função `next()` retorna o primeiro usuário cujo 'email' bate com o email da sessão.
    usuario = next((u for u in usuarios if u['email'] == session['usuario_logado']), None) 
    

    if not usuario:
        flash("Usuário não encontrado!", 'danger')
        return redirect(url_for('painel'))

    if request.method == 'POST':
        novo_nome = request.form.get('nome', usuario['nome'])
        novo_email = request.form.get('email', usuario['email'])
        novo_cpf = request.form.get('cpf', usuario['cpf'])
        nova_senha = request.form.get('nova_senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()

        if novo_email != usuario['email'] and any(u['email'] == novo_email for u in usuarios):
            flash("Este email já está em uso!", 'danger')
            return redirect(url_for('editar_usuario'))

        if novo_cpf != usuario['cpf'] and any(u['cpf'] == novo_cpf for u in usuarios):
            flash("CPF já cadastrado!", 'danger')
            return redirect(url_for('editar_usuario'))

        if nova_senha:
            if nova_senha != confirmar_senha:
                flash("As senhas não coincidem!", 'danger')
                return redirect(url_for('editar_usuario'))

            # Validação completa da senha (igual ao cadastro)
            if len(nova_senha) < 8 or len(nova_senha) > 12:
                flash('A senha deve ter entre 8 e 12 caracteres.', 'danger')
                return redirect(url_for('editar_usuario'))

            if not re.search(r'[A-Z]', nova_senha): #re ele vai analisar a senha e verificar se ela tem todos requisitos
                flash('A senha deve conter pelo menos uma letra maiúscula.', 'danger')
                return redirect(url_for('editar_usuario'))

            if not re.search(r'[a-z]', nova_senha):
                flash('A senha deve conter pelo menos uma letra minúscula.', 'danger')
                return redirect(url_for('editar_usuario'))

            if not re.search(r'[0-9]', nova_senha):
                flash('A senha deve conter pelo menos um número.', 'danger')
                return redirect(url_for('editar_usuario'))

            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', nova_senha):
                flash('A senha deve conter pelo menos um caractere especial.', 'danger')
                return redirect(url_for('editar_usuario'))

            usuario['senha'] = nova_senha

        usuario['nome'] = novo_nome
        usuario['email'] = novo_email
        usuario['cpf'] = novo_cpf

        session['nome_usuario'] = usuario['nome']
        session['usuario_logado'] = usuario['email']

        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('visualizar_usuario'))

    return render_template('editar_usuario.html', usuario=usuario)


# Visualizar perfil
@app.route('/usuario')
def visualizar_usuario():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    usuario = next((u for u in usuarios if u['email'] == session['usuario_logado']), None)
    # Procura na lista "usuarios" o primeiro usuário cujo email seja igual ao email da sessão (usuário logado).
    # A função next() retorna esse usuário, se encontrar.
    # Se não encontrar nenhum, retorna None para evitar erro.

    if not usuario:
        flash("Usuário não encontrado!", 'danger')
        return redirect(url_for('painel'))

    usuario_exibicao = {k: v for k, v in usuario.items() if k != 'senha'}        # k = chave ou key   v = value ou valor
    return render_template('visualizar_usuario.html', usuario=usuario_exibicao)


# Iniciar servidor
if __name__ == '__main__':
    app.run(debug=True)