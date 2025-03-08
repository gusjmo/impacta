from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:3899@localhost/barbearia'
db = SQLAlchemy(app)

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    servico = db.Column(db.String(50), nullable=False)
    profissional = db.Column(db.String(50), nullable=False)
    horario = db.Column(db.String(10), nullable=False)

    __table_args__ = (db.UniqueConstraint('profissional', 'horario', name='unique_profissional_horario'),)

def criar_banco():
    with app.app_context():
        db.create_all()

@app.route('/agendamentos', methods=['GET'])
def listar_agendamentos():
    agendamentos = Agendamento.query.all()
    return jsonify([{ 'id': a.id, 'nome': a.nome, 'telefone': a.telefone, 'servico': a.servico, 'profissional': a.profissional, 'horario': a.horario } for a in agendamentos])

@app.route('/agendamentos', methods=['POST'])
def cadastrar_agendamento():
    dados = request.json
    conflito = Agendamento.query.filter_by(horario=dados['horario'], profissional=dados['profissional']).first()
    if conflito:
        return jsonify({'erro': 'Horário já agendado para este profissional!'}), 400
    novo_agendamento = Agendamento(
        nome=dados['nome'], telefone=dados['telefone'], servico=dados['servico'], profissional=dados['profissional'], horario=dados['horario']
    )
    db.session.add(novo_agendamento)
    db.session.commit()
    return jsonify({'mensagem': 'Agendamento realizado com sucesso!'})

@app.route('/agendamentos/<int:id>', methods=['DELETE'])
def deletar_agendamento(id):
    agendamento = Agendamento.query.get(id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado!'}), 404
    db.session.delete(agendamento)
    db.session.commit()
    return jsonify({'mensagem': 'Agendamento excluído com sucesso!'})

@app.route('/agendamentos/delete_multiple', methods=['POST'])
def deletar_agendamentos():
    dados = request.json
    ids = dados.get('ids', [])
    if not ids:
        return jsonify({'erro': 'Nenhum agendamento selecionado para exclusão!'}), 400
    Agendamento.query.filter(Agendamento.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'mensagem': 'Agendamentos excluídos com sucesso!'})

@app.route('/horarios_disponiveis/<profissional>', methods=['GET'])
def listar_horarios_disponiveis(profissional):
    horarios_fixos = ['08:00', '08:40', '09:20', '10:00', '10:40', '11:20', '13:00', '13:40', '14:20', '15:00']
    horarios_ocupados = [a.horario for a in Agendamento.query.filter_by(profissional=profissional).all()]
    horarios_disponiveis = [h for h in horarios_fixos if h not in horarios_ocupados]
    return jsonify(horarios_disponiveis)

if __name__ == '__main__':
    try:
        criar_banco()
        print("Banco de dados conectado com sucesso!")
        app.run(debug=True)
    except Exception as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
