from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, date
from functools import wraps
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'barbearia-gusjmo-secret-2026')

# CORS restrito ao domínio de produção
CORS(app, origins=[
    "https://barbeariagusjmo.vercel.app",
    "http://localhost:5000",
    "http://127.0.0.1:5000"
])

# Configurando para usar SQLite
if os.environ.get("VERCEL"):
    # Vercel só permite escrita na pasta /tmp
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/barbearia.db'
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'barbearia.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Senha do admin — em produção use variável de ambiente
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1')

# Horários de atendimento disponíveis
HORARIOS_FIXOS = ['08:00', '08:40', '09:20', '10:00', '10:40', '11:20', '13:00', '13:40', '14:20', '15:00']

db = SQLAlchemy(app)

# Garante que o banco seja criado antes da primeira requisição (necessário no Vercel)
@app.before_request
def inicializar_banco():
    app.before_request_funcs[None].remove(inicializar_banco)
    db.create_all()

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    servico = db.Column(db.String(50), nullable=False)
    profissional = db.Column(db.String(50), nullable=False)
    data = db.Column(db.String(10), nullable=False, default=lambda: date.today().isoformat())
    horario = db.Column(db.String(10), nullable=False)
    pago = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.UniqueConstraint('profissional', 'horario', 'data', name='unique_profissional_horario_data'),
    )

def criar_banco():
    with app.app_context():
        db.create_all()

# ── Decorator de autenticação admin ──────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logado'):
            return jsonify({'erro': 'Acesso negado. Faça login como administrador.'}), 403
        return f(*args, **kwargs)
    return decorated

# ── Rotas de página ───────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/agendar')
def agendar():
    return render_template('agendar.html')

@app.route('/fila')
def fila():
    return render_template('fila.html')

@app.route('/agendamentos_view')
def agendamentos_view():
    if not session.get('admin_logado'):
        return redirect(url_for('login'))
    return render_template('agendamentos.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        dados = request.json
        if dados and dados.get('senha') == ADMIN_PASSWORD:
            session['admin_logado'] = True
            return jsonify({'mensagem': 'Login realizado com sucesso!'})
        return jsonify({'erro': 'Senha incorreta!'}), 401
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('admin_logado', None)
    return jsonify({'mensagem': 'Logout realizado com sucesso!'})

# ── API: Agendamentos ─────────────────────────────────────────────────────────
def mascarar_telefone(tel):
    """Mascara parte do telefone: 11985445588 → 1198***5588"""
    if len(tel) >= 8:
        return tel[:4] + '***' + tel[-4:]
    return tel

@app.route('/agendamentos', methods=['GET'])
def listar_agendamentos():
    data_filtro = request.args.get('data', date.today().isoformat())
    agendamentos = Agendamento.query.filter_by(data=data_filtro).order_by(Agendamento.horario).all()
    admin = session.get('admin_logado', False)
    return jsonify([
        {
            'id': a.id,
            'nome': a.nome,
            'telefone': a.telefone if admin else mascarar_telefone(a.telefone),
            'servico': a.servico,
            'profissional': a.profissional,
            'data': a.data,
            'horario': a.horario,
            'pago': a.pago
        } for a in agendamentos
    ])

@app.route('/agendamentos', methods=['POST'])
def cadastrar_agendamento():
    dados = request.json

    # Validação de campos obrigatórios
    campos_obrigatorios = ['nome', 'telefone', 'servico', 'profissional', 'horario']
    for campo in campos_obrigatorios:
        if not dados or not dados.get(campo) or not str(dados[campo]).strip():
            return jsonify({'erro': f'Campo obrigatório ausente: {campo}'}), 400

    data_agendamento = dados.get('data', date.today().isoformat())

    # Verifica conflito de horário
    conflito = Agendamento.query.filter_by(
        horario=dados['horario'],
        profissional=dados['profissional'],
        data=data_agendamento
    ).first()
    if conflito:
        return jsonify({'erro': 'Horário já agendado para este profissional nessa data!'}), 400

    # Valida horário
    if dados['horario'] not in HORARIOS_FIXOS:
        return jsonify({'erro': 'Horário inválido!'}), 400

    novo_agendamento = Agendamento(
        nome=dados['nome'].strip(),
        telefone=dados['telefone'].strip(),
        servico=dados['servico'].strip(),
        profissional=dados['profissional'].strip(),
        data=data_agendamento,
        horario=dados['horario']
    )
    db.session.add(novo_agendamento)
    db.session.commit()
    return jsonify({
        'mensagem': 'Agendamento realizado com sucesso!',
        'id': novo_agendamento.id,
        'nome': novo_agendamento.nome,
        'profissional': novo_agendamento.profissional,
        'data': novo_agendamento.data,
        'horario': novo_agendamento.horario
    })

@app.route('/agendamentos/<int:id>', methods=['DELETE'])
@admin_required
def deletar_agendamento(id):
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado!'}), 404
    db.session.delete(agendamento)
    db.session.commit()
    return jsonify({'mensagem': 'Agendamento excluído com sucesso!'})

@app.route('/agendamentos/<int:id>/pagar', methods=['PUT'])
@admin_required
def confirmar_pagamento(id):
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado!'}), 404
    agendamento.pago = True
    db.session.commit()
    return jsonify({'mensagem': 'Pagamento confirmado com sucesso!'})

# ── API: Fila ─────────────────────────────────────────────────────────────────
@app.route('/fila_cliente', methods=['GET'])
def fila_cliente():
    nome_cliente = request.args.get('nome')
    data_filtro = request.args.get('data', date.today().isoformat())

    if not nome_cliente:
        return jsonify({'erro': 'Nome do cliente não informado!'}), 400

    # Busca por nome (case-insensitive) na data informada
    agendamento = Agendamento.query.filter(
        Agendamento.nome.ilike(f'%{nome_cliente}%'),
        Agendamento.data == data_filtro
    ).first()

    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado para esse nome na data informada'}), 404

    # Ordena fila do mesmo profissional na mesma data
    agendamentos_fila = sorted(
        Agendamento.query.filter_by(profissional=agendamento.profissional, data=data_filtro).all(),
        key=lambda x: datetime.strptime(x.horario, '%H:%M')
    )

    posicao = next((i for i, a in enumerate(agendamentos_fila) if a.id == agendamento.id), -1)
    tempo_estimado = posicao * 40

    return jsonify({
        'nome': agendamento.nome,
        'profissional': agendamento.profissional,
        'horario': agendamento.horario,
        'data': agendamento.data,
        'posicao': posicao + 1,
        'pessoas_na_frente': posicao,
        'tempo_estimado_minutos': tempo_estimado
    })

# ── API: Horários ─────────────────────────────────────────────────────────────
@app.route('/horarios_disponiveis/<profissional>', methods=['GET'])
def listar_horarios_disponiveis(profissional):
    data_filtro = request.args.get('data', date.today().isoformat())
    horarios_ocupados = [
        a.horario for a in Agendamento.query.filter_by(profissional=profissional, data=data_filtro).all()
    ]
    horarios_disponiveis = [h for h in HORARIOS_FIXOS if h not in horarios_ocupados]
    return jsonify(horarios_disponiveis)

# ── API: Stats (unificado) ────────────────────────────────────────────────────
@app.route('/stats', methods=['GET'])
def stats():
    data_filtro = request.args.get('data', date.today().isoformat())
    total = Agendamento.query.filter_by(data=data_filtro).count()

    agendamentos_ordenados = Agendamento.query.filter_by(data=data_filtro).order_by(Agendamento.horario).all()
    proximo = None
    if agendamentos_ordenados:
        p = agendamentos_ordenados[0]
        proximo = {
            'nome': p.nome,
            'profissional': p.profissional,
            'horario': p.horario,
            'data': p.data
        }

    # Agendamentos por profissional (para dashboard)
    por_profissional = {}
    for a in Agendamento.query.filter_by(data=data_filtro).all():
        por_profissional[a.profissional] = por_profissional.get(a.profissional, 0) + 1

    return jsonify({
        'total': total,
        'proximo': proximo,
        'por_profissional': por_profissional
    })

# Manter retrocompatibilidade com rotas antigas
@app.route('/fila_total', methods=['GET'])
def fila_total():
    total = Agendamento.query.count()
    return jsonify({'total': total})

@app.route('/agendamentos_total', methods=['GET'])
def agendamentos_total():
    total = Agendamento.query.count()
    return jsonify({'total': total})

@app.route('/proximo_atendimento', methods=['GET'])
def proximo_atendimento():
    data_hoje = date.today().isoformat()
    agendamentos = Agendamento.query.filter_by(data=data_hoje).order_by(Agendamento.horario).all()
    if not agendamentos:
        return jsonify({})
    proximo = agendamentos[0]
    return jsonify({
        'nome': proximo.nome,
        'profissional': proximo.profissional,
        'horario': proximo.horario,
        'data': proximo.data
    })

if __name__ == '__main__':
    try:
        criar_banco()
        print("Banco de dados conectado com sucesso!")
        debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
        app.run(debug=debug_mode)
    except Exception as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
