from flask import Flask, request, jsonify
from sqlalchemy import select
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash # Importe chec


from models import *

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = '12345@Z'
JWT = JWTManager(app)

import random
import string

def gerar_codigo_aleatorio(tamanho=5):
    caracteres = string.digits
    codigo = ''.join(random.choice(caracteres) for _ in range(tamanho))
    return codigo

# Exemplo de uso:
access_token = gerar_codigo_aleatorio()
print(access_token)


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        current_user = get_jwt_identity()
        try:
            sql = select(Usuario).where(Usuario.id == current_user)
            usuario = db_session.execute(sql).scalar()
            if usuario and usuario.papel == "admin":
                return fn(*args, **kwargs)
            return jsonify({"msg": "acesso negado, privilegio de administrador"}), 403
        finally:
            db_session.close()
    return wrapped

@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    email = dados.get('email')
    senha = dados.get('senha')

    if not email or not senha:
        return jsonify({"Msg": "Dados incompletos"}), 400

    usuario = db_session.query(Usuario).filter_by(email=email).first()

    if usuario and usuario.check_password(senha):
        access_token = create_access_token(identity=usuario.nome)
        return jsonify({'nome': usuario.nome, 'email': usuario.email, 'access_token': access_token}), 200

    return jsonify({"Msg": "Credenciais inválidas"}), 401

@app.route('/')
def index():
    return jsonify("Hello, World!")


@app.route('/cadastro_usuario', methods=['POST'])
def cadastro_usuario():
    try:
        dados_usuarios = request.get_json()

        # Validação dos dados
        if not all(key in dados_usuarios for key in ['nome', 'cpf', 'email', 'password', 'papel']):
            return jsonify({"mensagem": "Dados inválidos ou incompletos"}), 400

        novo_usuario = Usuario(
            nome=dados_usuarios['nome'],
            cpf=dados_usuarios['cpf'],
            email=dados_usuarios['email'],
            password=generate_password_hash(dados_usuarios['password']),  # Hash da senha
            papel=dados_usuarios['papel'],
        )

        novo_usuario.save()
        return jsonify({"mensagem": "Cliente cadastrado com sucesso"}), 201
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"mensagem": "Erro interno do servidor"}), 500


@app.route('/listarUsuario', methods=['GET'])
def listar_usuario():
    try:
        lista_usuarios = db_session.query(Usuario).all()
        resultado = [usuarios.serialize() for usuarios in lista_usuarios]
        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro ao listar usuario: {e}")
        return jsonify({"mensagem": "Erro ao obter clientes"}), 500


@app.route('/BuscaClientes/id/<int:cliente_id>/servicos', methods=['GET'])
def get_servicos_cliente(cliente_id):
    """
       rota para buscar o cliente (filtro para buscar o servico cadastrado do cliente)

       ## Endpoint:
       /BuscaClientes/id/cliente_id/servicos

       ## Parâmetros:
       cliente_id: id do cliente

       ## Resposta (JSON):
	    {
		"data_abertura": "2025-07-26",
		"descricao_servico": "Limpeza",
		"id_servico": 2,
		"status": "Aberto",
		"valor_estimado": 150,
		"veiculo_id": 1
	    }
       ```

       ## Erros possíveis:
       se o valor for errado ou não existe error 500
       ```json
       {
           "erro": "Formato de data inválido. string
       }
       ```
       """
    try:
        servicos = OrdemServico.query.join(Veiculo).filter(
            Veiculo.cliente_id == cliente_id
       ).all()
        return jsonify([servico.serialize() for servico in servicos])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/adicionarClientes', methods=['POST'])
def adicionar_cliente():
    """
       rota para adicionar um cliente

       ## Endpoint:
       /adicionarClientes

       ## Resposta (JSON):
        {
        "nome": "slaMan",
        "cpf": "12445674310",
        "telefone": "12291422138",
        "endereco": "Centro 3"
        }

       ## Erros possíveis:
       "mensagem": Dados inválidos ou incompletos 400
       "mensagem": CPF já cadastrado 409
       "mensagem": Telefone já cadastrado 409
       "mensagem": Erro interno do servidor 500
    """
    try:
        dados_cliente = request.get_json()

        cpf = dados_cliente['cpf']
        telefone = dados_cliente['telefone']

        # Verifica se CPF já existe
        cpf_existente = db_session.execute(select(Cliente).where(Cliente.cpf == cpf)).scalar()
        if cpf_existente:
            return jsonify({"mensagem": "CPF já cadastrado"}), 409

        # Verifica se telefone já existe
        telefone_existente = db_session.execute(select(Cliente).where(Cliente.telefone == telefone)).scalar()
        if telefone_existente:
            return jsonify({"mensagem": "Telefone já cadastrado"}), 409

        novo_cliente = Cliente(
            nome=dados_cliente['nome'],
            cpf=cpf,
            telefone=telefone,
            endereco=dados_cliente['endereco']
        )
        novo_cliente.save()
        return jsonify({"mensagem": "Cliente cadastrado com sucesso"}), 201
    except (TypeError, KeyError) as e:
        print(f"Erro ao adicionar cliente: {e}")
        return jsonify({"mensagem": "Dados inválidos ou incompletos"}), 400
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"mensagem": "Erro interno do servidor"}), 500


@app.route('/listarClientes', methods=['GET'])
def listar_clientes():
    """
       rota para adicionar listar o cliente

       ## Endpoint:
       /listarClientes

       ## Resposta (JSON):
        {
		"cpf": "12345674310",
		"endereco": "Centro 3",
		"id_cliente": 1,
		"nome": "pedro",
		"telefone": "18291422138"
	    }


       ## Erros possíveis:
       "mensagem": Erro interno do servidor 500

       """
    try:
        lista_clientes = db_session.query(Cliente).all()
        resultado = [cliente.serialize() for cliente in lista_clientes]
        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro ao listar clientes: {e}")
        return jsonify({"mensagem": "Erro ao obter clientes"}), 500


@app.route("/editarClients/<int:cliente_id>", methods=['PUT'])
def editar_clientes(cliente_id):
    """
       rota para editar um cliente

       ## Endpoint:
       /editarClients/cliente_id

       ## Resposta (JSON):
        {
	    "nome": "ruyDaoter",
	    "cpf": "22345674310",
	    "telefone": "18991423132",
	    "endereco": "rua paubaixo"
        }


       ## Erros possíveis:
        mensagem: Usuario não encontrado 404

       """
    cliente = db_session.execute(select(Cliente).where(Cliente.id_cliente == cliente_id)).scalar()

    if cliente is None:
        return jsonify({"mensagem": "Usuario nõo encontrado"})

    dados_cliente = request.get_json()
    nome = dados_cliente['nome']
    cpf = dados_cliente['cpf']
    telefone = dados_cliente['telefone']
    endereco = dados_cliente['endereco']

    cliente.nome = nome
    cliente.cpf = cpf
    cliente.telefone = telefone
    cliente.endereco = endereco

    cliente.save()
    return jsonify({"mensagem": "cliente editado com sucesso"})

@app.route("/ocultarClient/<int:cliente_id>", methods=['PUT'])
def ocultar_cliente(cliente_id):
    cliente = db_session.execute(select(Cliente).where(Cliente.id_cliente == cliente_id)).scalar()

    if cliente is None:
        return jsonify({"mensagem": "Cliente não encontrado"}), 404

    dados = request.get_json()
    motivo = dados.get("motivo")

    if not motivo:
        return jsonify({"mensagem": "Motivo é obrigatório"}), 400

    cliente.ativo = False
    cliente.motivo_inativo = motivo

    cliente.save()
    return jsonify({"mensagem": "Cliente ocultado com sucesso"})


@app.route("/deletarCliente/<int:cliente_id>", methods=['DELETE'])
def deletar_cliente(cliente_id):
    try:
        cliente = db_session.query(Cliente).get(cliente_id)
        if not cliente:
            return jsonify({"message": "Cliente não encontrado"}), 404


        db_session.delete(cliente)
        db_session.commit()
        return jsonify({"message": "Cliente excluído com sucesso"}), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao excluir Cliente: {str(e)}"}), 500




@app.route('/adicionarVeiculo', methods=['POST'])
def adicionar_veiculo():
    """
             rota para adicionar um Veiculo

             ## Endpoint:
             /adicionarVeiculo

             ## Resposta (JSON):
             {
	            "mensagem": "Veículo cadastrado com sucesso"
            }


             ## Erros possíveis:


             "mensagem": Erro interno do servidor 500

             "mensagem": Dados inválidos ou incompletos 400

             """
    try:
        dados_veiculo = request.get_json()
        novo_veiculo = Veiculo(
            cliente_id=dados_veiculo['cliente_id'],
            marca=dados_veiculo['marca'],
            modelo=dados_veiculo['modelo'],
            placa=dados_veiculo['placa'],
            ano_fabricacao=dados_veiculo['ano_fabricacao']
        )
        novo_veiculo.save()
        return jsonify({"mensagem": "Veículo cadastrado com sucesso"}), 201
    except (TypeError, KeyError) as e:
        print(f"Erro ao adicionar veículo: {e}")
        return jsonify({"mensagem": "Dados inválidos ou incompletos"}), 400
    except Exception as e:
        print(f"Erro ao adicionar veículo: {e}")
        return jsonify({"mensagem": "Erro interno do servidor"}), 500



@app.route('/listarVeiculos', methods=['GET'])
def listar_veiculos():
    """
                rota para listar um veiculo

                ## Endpoint:
                /listarVeiculos

                ## Resposta (JSON):
                {
                    "ano_fabricacao": 2008,
                    "cliente_id": 1,
                    "id_veiculo": 2,
                    "marca": "Volkswagen",
                    "modelo": "Gol G4",
                    "placa": "OsRlq444"
                }


                ## Erros possíveis:


                "mensagem": Erro ao obter veiculos 500



                """
    try:
        lista_veiculos = db_session.query(Veiculo).all()
        resultado = [veiculo.serialize() for veiculo in lista_veiculos]
        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro ao listar veículos: {e}")
        return jsonify({"mensagem": "Erro ao obter veículos"}), 500


@app.route("/editarVeiculos/<int:id_veiculo>", methods=['PUT'])
def editar_veiculos(id_veiculo):
    """
            rota para editar um Veiculo

                 ## Endpoint:
                 /editarVeiculos/id_veiculo

                 ## Resposta (JSON):
                 {
                    "mensagem": "veiculo editado com sucesso"
                }
    """
    veiculos = db_session.execute(select(Veiculo).where(Veiculo.id_veiculo == id_veiculo)).scalar()

    if veiculos is None:
        return jsonify({"mensagem": "Veiculo nõo encontrado"})

    dados_veiculo = request.get_json()
    marca = dados_veiculo['marca']
    modelo = dados_veiculo['modelo']
    placa = dados_veiculo['placa']
    ano_fabricacao = dados_veiculo['ano_fabricacao']

    veiculos.marca = marca
    veiculos.modelo = modelo
    veiculos.placa = placa
    veiculos.ano_fabricacao = ano_fabricacao

    veiculos.save()
    return jsonify({"mensagem": "veiculo editado com sucesso"})

@app.route("/deletarVeiculos/<int:id_veiculo>", methods=['DELETE'])
def veiculos(id_veiculo):
    try:
        veiculo = db_session.query(Veiculo).get(id_veiculo)
        if veiculo is None:
            return jsonify({"message": "veiculo não encontrado"}), 404

        db_session.delete(veiculo)
        db_session.commit()
        return jsonify({"message": "veiculo excluído com sucesso"}), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao excluir veiculo: {str(e)}"}), 500





@app.route('/adicionarOrdemServico', methods=['POST'])
def adicionar_ordem_servico():
#segurança
    """
            rota para adicionar uma Ordem de Servico

                 ## Endpoint:
                 /adicionarOrdemServico

                 ## Resposta (JSON):
                 mensagem": "Ordem de serviço cadastrada com sucesso"

                 ## Erros possíveis:
                 400 invalido
                 500 erro interno
    """
    try:
        dados_ordem = request.get_json()
        nova_ordem = OrdemServico(
            veiculo_id=dados_ordem['veiculo_id'],
            data_abertura=dados_ordem['data_abertura'],
            descricao_servico=dados_ordem['descricao_servico'],
            status=dados_ordem['status'],
            valor_estimado=dados_ordem['valor_estimado']
        )
        nova_ordem.save()
        return jsonify({"mensagem": "Ordem de serviço cadastrada com sucesso"}), 201
    except (TypeError, KeyError) as e:
        print(f"Erro ao adicionar ordem de serviço: {e}")
        return jsonify({"mensagem": "Dados inválidos ou incompletos"}), 400
    except Exception as e:
        print(f"Erro ao adicionar ordem de serviço: {e}")
        return jsonify({"mensagem": "Erro interno do servidor"}), 500


@app.route('/listarOrdemServicos', methods=['GET'])
#liberado
def listar_ordem_servicos():
    """
            rota para listar uma Ordem Servico

                 ## Endpoint:
                 /listarOrdemServicos

                 ## Resposta (JSON):
                 {
                    "data_abertura": "2025-07-26",
                    "descricao_servico": "Troca de óleo e filtro e consertar o lataria",
                    "id_servico": 1,
                    "status": "Fechado",
                    "valor_estimado": 750,
                    "veiculo_id": 2
                }


                 ## Erros possíveis:
                 500 erro ao obter ordens de servico
    """
    try:
        lista_ordens = db_session.query(OrdemServico).all()
        resultado = [ordem.serialize() for ordem in lista_ordens]
        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro ao listar ordens de serviço: {e}")
        return jsonify({"mensagem": "Erro ao obter ordens de serviço"}), 500

@app.route("/editarServico/<int:id_servico>", methods=['PUT'])
#segurança
def editar_servico(id_servico):
    """
              rota para ediar uma Ordem de Servico

                   ## Endpoint:
                   /editarServico/id_Servico

                   ## Resposta (JSON):
                   {
                      "data_abertura": "2025-07-26",
                      "descricao_servico": "Troca de óleo e filtro e consertar o lataria",
                      "id_servico": 1,
                      "status": "Fechado",
                      "valor_estimado": 750,
                      "veiculo_id": 2
                  }


    """

    ordens_servico = db_session.execute(select(OrdemServico).where(OrdemServico.id_servico == id_servico)).scalar()

    if ordens_servico is None:
        return jsonify({"mensagem": "Serviço nõo encontrado"})

    dados_ordem = request.get_json()
    data_abertura = dados_ordem['data_abertura']
    descricao_servico = dados_ordem['descricao_servico']
    status = dados_ordem['status']
    valor_estimado = dados_ordem['valor_estimado']

    ordens_servico.data_abertura = data_abertura
    ordens_servico.descricao_servico = descricao_servico
    ordens_servico.status = status
    ordens_servico.valor_estimado = valor_estimado

    ordens_servico.save()
    return jsonify({"mensagem": "Serviço editado com sucesso"})


@app.route("/deletarServico/<int:id_servico>", methods=['DELETE'])
def deletar_servico(id_servico):
    try:
        servico = db_session.query(OrdemServico).get(id_servico)
        if servico is None:
            return jsonify({"message": "Usuário não encontrado"}), 404

        db_session.delete(servico)
        db_session.commit()
        return jsonify({"message": "Usuário excluído com sucesso"}), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao excluir usuário: {str(e)}"}), 500



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
