from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'chave_secreta_solidez'

# Banco de dados simulado
usuarios = []
transacoes_db = []
investimentos_db = []

def extrato_por_data(item):
        return item['data']

# Variáveis globais acessíveis nos templates
# Este decorador @app.context_processor define uma função que injeta variáveis globais nos templates HTML.
# Assim, as variáveis 'now' (data e hora atual) e 'datetime' (módulo completo) estarão disponíveis automaticamente
# em todos os arquivos .html renderizados, sem precisar passá-las manualmente com render_template.
@app.context_processor
def inject():
    def formatar_data(data):
        if isinstance(data, datetime):
            return data.strftime('%d/%m/%Y')
        try:
            return datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')
        except:
            return data
    return dict(formatar_data=formatar_data)

# Rota inicial
@app.route('/')
def index():
    if 'usuario_logado' not in session:
        return render_template('index.html')
    return render_template('index.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        # Procura na lista "usuarios" o primeiro usuário cujo email seja igual ao email da sessão (usuário logado).
        # Se não encontrar nenhum, retorna None para evitar erro.
        usuario = None
        for u in usuarios:
            if u['email'] == email and u['senha'] == senha:
                usuario = u
                break

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
        nome       = request.form.get('nome')
        email      = request.form.get('email')
        cpf        = request.form.get('cpf')
        senha      = request.form.get('senha', '').strip()
        confirmar  = request.form.get('confirmar', '').strip()

        # conferência de senhas
        if senha != confirmar:
            flash('As senhas não coincidem!', 'danger')
            return redirect(url_for('cadastro'))

        #email já cadastrado?
        for u in usuarios:
            if u['email'] == email:
                flash('Email já cadastrado!', 'danger')
                return redirect(url_for('cadastro'))

        #CPF já cadastrado?
        for u in usuarios:
            if u['cpf'] == cpf:
                flash('CPF já cadastrado!', 'danger')
                return redirect(url_for('cadastro'))

        #comprimento da senha
        if len(senha) < 8 or len(senha) > 12:
            flash('A senha deve ter entre 8 e 12 caracteres.', 'danger')
            return redirect(url_for('cadastro'))

        #validação de complexidade da senha
        maiuscula = False
        minuscula = False
        numero = False
        caracterpcd = False
        for s in senha:
            if s.isupper():
                maiuscula = True
            if s.islower():
                minuscula = True
            if s.isdigit():
                numero = True
            if not s.isalnum():
                caracterpcd = True

        if not (maiuscula and minuscula and numero and caracterpcd):
            flash(
                'A senha deve conter ao menos uma letra maiúscula, '
                'uma letra minúscula, um número e um caractere especial.',
                'danger'
            )
            return redirect(url_for('cadastro'))

        #tudo ok: cria o usuário
        usuarios.append({
            'nome':      nome,
            'email':     email,
            'cpf':       cpf,
            'senha':     senha,
            'saldo':     0,
            'investido': 0
        })
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('cadastro.html')


@app.route('/painel')
def painel():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    nome_usuario = session['nome_usuario'].title()
    usuario_email = session['usuario_logado']
    usuario = None
    for u in usuarios:
        if u['email'] == usuario_email:
            usuario = u
            break


    if not usuario:
        flash("Usuário não encontrado!", 'danger')
        return redirect(url_for('login'))

    # Filtra transações e investimentos
    # Transações
    transacoes = []
    for t in transacoes_db:
        if t['usuario'] == usuario_email:
            transacoes.append(t)

    # Investimentos
    investimentos = []
    for i in investimentos_db:
        if i['usuario'] == usuario_email:
            investimentos.append(i)

    # Totais
    # Calcula total de entradas
    total_entrada = 0
    for t in transacoes:
        if t['tipo'] == 'entrada':
            total_entrada += t['valor']

    # Calcula total de saídas
    total_saida = 0
    for t in transacoes:
        if t['tipo'] == 'saida':
            total_saida += t['valor']

    # Calcula total investido
    total_investido = 0
    for i in investimentos:
        total_investido += i['valor']

    saldo = total_entrada - total_saida - total_investido

    session['saldo'] = saldo

    # Monta o extrato combinando entradas, saídas e investimentos
    extrato = []
    for t in transacoes:
        extrato.append({
            'data':t['data'],
            'tipo':t['tipo'],
            'valor':t['valor'],
            'descricao':t['descricao']
        })
        
    for i in investimentos:
        extrato.append({
            'data':i['data'],
            'tipo':'investimento',
            'valor':i['valor'],
            'descricao':i['local_descricao']
        })

    # Define uma função de chave em vez de lambda
    
    extrato.sort(key=extrato_por_data, reverse=True)

    extrato = extrato[:5]

    return render_template(
        'painel.html',
        nome_usuario=nome_usuario,
        saldo=saldo,
        total_entrada=total_entrada,
        total_saida=total_saida,
        total_investido=total_investido,
        extrato=extrato         # ← envia o extrato completo ao template
    )

@app.route('/transacoes', methods=['GET', 'POST'])
def transacoes():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))

    email_usuario = session['usuario_logado']
    transacao_em_edicao = None

    # Captura ?tipo=entrada|saida para pré-selecionar o <select>
    tipo_predefinido = request.args.get('tipo', '')

    # --- EDITAR TRANSACAO (clicou no botão “Editar”) ---
    if request.method == 'POST' and 'editar_id' in request.form and not request.form.get('data'):
        editar_id = request.form.get('editar_id')

        for t in transacoes_db:
            if t.get('id') == editar_id and t['usuario'] == email_usuario:
                transacao_em_edicao = t
                break


    # --- EXCLUIR TRANSACAO ---
    if request.method == 'POST' and 'excluir_id' in request.form:
        excluir_id = request.form.get('excluir_id')

        for i, t in enumerate(transacoes_db):
            if t.get('id') == excluir_id and t['usuario'] == email_usuario:
                del transacoes_db[i]
                flash('Transação excluída com sucesso!', 'success')
                return redirect(url_for('transacoes'))


    # --- SALVAR OU ATUALIZAR TRANSACAO ---
    if request.method == 'POST' and request.form.get('data'):
        data = datetime.strptime(request.form.get('data'), '%Y-%m-%d').strftime('%Y-%m-%d')
        descricao = request.form.get('descricao')
        tipo = request.form.get('tipo')
        valor = float(request.form.get('valor', 0))


        if tipo not in ['entrada', 'saida'] or valor <= 0:
            flash('Tipo de transação inválido ou valor não positivo.', 'danger')
            return redirect(url_for('transacoes'))


        editar_id = request.form.get('editar_id')
        
        if editar_id:
            # Atualiza existente
            for t in transacoes_db:
                if t.get('id') == editar_id and t['usuario'] == email_usuario:
                    t['data'] = data
                    t['descricao'] = descricao
                    t['tipo'] = tipo
                    t['valor'] = valor
                    flash('Transação atualizada com sucesso!', 'success')
                    return redirect(url_for('transacoes'))
                
        else:
            # Cria nova
            transacoes_db.append({
                'id': str(uuid4()),
                'usuario': email_usuario,
                'data': data,
                'descricao': descricao,
                'tipo': tipo,
                'valor': valor
            })
            flash('Transação registrada com sucesso!', 'success')
            return redirect(url_for('transacoes'))


    # Filtra transações do usuário
    transacoes_usuario = []

    for t in transacoes_db:
        if t['usuario'] == email_usuario:
            transacoes_usuario.append(t)

    # Filtra investimentos do usuário
    investimentos_usuario = []

    for i in investimentos_db:
        if i['usuario'] == email_usuario:
            investimentos_usuario.append(i)

    extrato = []

    for t in transacoes_usuario:
        extrato.append({
            'id':t['id'],
            'data':t['data'],
            'tipo':t['tipo'],
            'valor':t['valor'],
            'descricao':t['descricao']
        })

    for i in investimentos_usuario:
        extrato.append({
            'data': i['data'],
            'tipo': 'investimento',
            'valor': i['valor'],
            'descricao': i['local_descricao']
        })

    extrato.sort(key=extrato_por_data, reverse=True)

    return render_template(
        'transacoes.html',
        transacao_em_edicao=transacao_em_edicao,
        tipo_predefinido=tipo_predefinido,
        extrato=extrato
    )

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
    
    usuario = None
    for u in usuarios:
        if u['email'] == session['usuario_logado']:
            usuario = u
            break
        
    if not usuario:
        flash("Usuário não encontrado!", 'danger')
        return redirect(url_for('painel'))

    if request.method == 'POST':
        novo_nome = request.form.get('nome', usuario['nome'])
        novo_email = request.form.get('email', usuario['email'])
        novo_cpf = request.form.get('cpf', usuario['cpf'])
        nova_senha = request.form.get('nova_senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()

        if novo_email != usuario['email']:
            for u in usuarios:
                if u['email'] == novo_email:
                    flash("Este email já está em uso!", 'danger')
                    return redirect(url_for('editar_usuario'))

        if novo_cpf != usuario['cpf']:
            for u in usuarios:
                if u['cpf'] == novo_cpf:
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

            maiuscula = False
            minuscula = False
            numero = False
            caracterpcd = False
            for s in nova_senha:
                if s.isupper():
                   maiuscula = True
                if s.islower():
                    minuscula = True
                if s.isdigit():
                    numero = True
                if not s.isalnum():
                    caracterpcd = True

            if not (maiuscula and minuscula and numero and caracterpcd):
                flash(
                    'A senha deve conter ao menos uma letra maiúscula, '
                    'uma letra minúscula, um número e um caractere especial.',
                    'danger'
                )
                return render_template('editar_usuario.html', usuario=usuario)

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

    usuario = None
    for u in usuarios:
        if u['email'] == session['usuario_logado']:
            usuario = u
            break

    if not usuario:
        flash("Usuário não encontrado!", 'danger')
        return redirect(url_for('painel'))

    usuario_exibicao = {}
    for k, v in usuario.items():
        if k != 'senha':
            usuario_exibicao[k] = v
    return render_template('visualizar_usuario.html', usuario=usuario_exibicao)


#investimento
@app.route('/investimento', methods=['GET', 'POST'])
def investimento():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))
    
    email_usuario = session['usuario_logado']  # sempre disponível
    data = request.form.get('data') or datetime.now().strftime('%Y-%m-%d')  # valor padrão

    if request.method == 'POST':
        valor = float(request.form.get('valor', 0))
        local_descricao = request.form.get('local_descricao', '').strip()

        if valor <= 0:
            flash('O valor do investimento deve ser maior que zero.', 'danger')
            return redirect(url_for('investimento'))

        # Salva o novo investimento
        investimentos_db.append({
            'id': str(uuid4()),
            'usuario': email_usuario,
            'valor': valor,
            'local_descricao': local_descricao,
            'data': data,
            'data_registro': datetime.now().strftime('%Y-%m-%d')
        })

        # Atualiza o valor total investido no usuário
        for usuario in usuarios:
            if usuario['email'] == email_usuario:
                usuario['investido'] = usuario.get('investido', 0) + valor
                break

        return redirect(url_for('investimento'))

    # Recupera os investimentos do usuário para exibição na tabela
    investimentos_usuario = []
    for i in investimentos_db:
        if i['usuario'] == email_usuario:
            investimentos_usuario.append(i)

    return render_template(
        'investimento.html',
        data_padrao=datetime.now().strftime('%Y-%m-%d'),
        investimentos=investimentos_usuario
    )

#emergencia
@app.route('/emergencia', methods=['GET', 'POST'])
def emergencia():
    if 'usuario_logado' not in session:
        return redirect(url_for('login'))
    
    resultado = None

    if request.method == 'POST':
        try:
            despesa_mensal = float(request.form.get('despesa_mensal', 0))
            meses_cobertura = int(request.form.get('meses_cobertura', 0))
            prazo = int(request.form.get('prazo', 0))

            if despesa_mensal <= 0:
                flash('A despesa mensal deve ser maior que zero', 'danger')
            elif meses_cobertura <= 0:
                flash('Os meses de cobertura devem ser maiores que zero', 'danger')
            elif prazo <= 0:
                flash('O prazo deve ser maior que zero', 'danger')
            else:
                reserva_total = despesa_mensal * meses_cobertura
                reserva_mensal = reserva_total / prazo

                resultado = {
                    'reserva_total': f"{reserva_total:.2f}",
                    'reserva_mensal': f"{reserva_mensal:.2f}",
                    'meses_cobertura': meses_cobertura,
                    'prazo': prazo,
                    'despesa_mensal': f"{despesa_mensal:.2f}"
                }
        except ValueError:
            flash('Por favor, insira valores numéricos válidos', 'danger')
        except Exception as e:
            mensagem_erro = 'Erro no cálculo de emergência: ' + str(e)
            app.logger.error(mensagem_erro)
            flash('Ocorreu um erro ao calcular sua reserva de emergência', 'danger')

    return render_template('emergencia.html', resultado=resultado)

# Iniciar servidor
if __name__ == '__main__':
    app.run(debug=True)