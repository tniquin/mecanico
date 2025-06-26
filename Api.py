from flask import Flask, request, jsonify
from sqlalchemy import select
from flask_jwt_extended import create_access_token, get_jwt_identity, JWTManager, jwt_required
from functools import wraps
from BancoDeDadosMecanica import *
from datetime import datetime
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = '12345@Z'
JWT = JWTManager(app)



def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        current_user = get_jwt_identity()
        try:
            sql = select(Usuario).where(Usuario.id == current_user)
            print("Usuário autenticado ID:", current_user)
            usuario = db_session.execute(sql).scalar()
            if usuario and usuario.papel == "admin":
                return fn(*args, **kwargs)
            print("Token gerado para ID:", usuario.id)

            return jsonify({"msg": "acesso negado, privilegio de administrador"}), 403
        finally:
            db_session.close()
    return wrapped
# permite acesso se o usuário for o dono dos dados OU for admin.
#def owner_or_admin_required(param_id_name):
    #def decorator(fn):
        #@wraps(fn)
        #def wrapper(*args, **kwargs):
            #user_id = get_jwt_identity()
           # recurso_id = kwargs.get(param_id_name)

           # try:
             #   usuario = db_session.query(Usuario).get(user_id)
              #  if not usuario:
              #      return jsonify({"mensagem": "Usuário inválido"}), 401

              #  if usuario.papel == 'admin' or int(user_id) == int(recurso_id):
               #     return fn(*args, **kwargs)

               # return jsonify({"mensagem": "Acesso negado: não é dono nem admin"}), 403

         #   finally:
             #   db_session.close()
   #     return wrapper
 #  return decorator

@app.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    email = dados.get('email')
    senha = dados.get('senha')

    if not email or not senha:
        return jsonify({"msg": "Dados incompletos"}), 400

    usuario = db_session.query(Usuario).filter_by(email=email).first()

    if usuario and usuario.check_password(senha):
        access_token = create_access_token(identity=str(usuario.id))  # <-- string aqui!
        return jsonify({
            'nome': usuario.nome,
            'email': usuario.email,
            'access_token': access_token
        }), 200

    return jsonify({"msg": "Credenciais inválidas"}), 401

@app.route('/')
def index():
    return jsonify("Hello, World!")


@app.route('/cadastro_usuario', methods=['POST'])
def cadastro_usuario():
    try:
        dados_usuarios = request.get_json()

        campos_obrigatorios = ['nome', 'cpf', 'email', 'password']
        for campo in campos_obrigatorios:
            if campo not in dados_usuarios or not dados_usuarios[campo]:
                return jsonify({"mensagem": f"Campo '{campo}' é obrigatório."}), 400

        novo_usuario = Usuario(
            nome=dados_usuarios['nome'],
            cpf=dados_usuarios['cpf'],
            email=dados_usuarios['email'],
            password=generate_password_hash(dados_usuarios['password']),
            papel=dados_usuarios['papel'],
        )

        novo_usuario.save()
        return jsonify({"mensagem": "Usuário cadastrado com sucesso"}), 201

    except Exception as e:
        db_session.rollback()
        print(f"Erro inesperado: {e}")
        return jsonify({"mensagem": f"Erro interno: {str(e)}"}), 500


@app.route('/listarUsuario', methods=['GET'])
@jwt_required()
def listar_usuario():
    try:
        lista_usuarios = db_session.execute(select(Usuario)).scalars().all()
        resultado = [usuarios.serialize() for usuarios in lista_usuarios]
        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro ao listar usuario: {e}")
        return jsonify({"mensagem": "Erro ao obter clientes"}), 500


@app.route('/BuscaClientes/id/<int:cliente_id>/servicos', methods=['GET'])
@jwt_required()
def get_servicos_cliente(cliente_id):
    try:
        servicos = OrdemServico.query.join(Veiculo).filter(
            Veiculo.cliente_id == cliente_id
       ).all()
        return jsonify([servico.serialize() for servico in servicos])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/alterarStatusCliente/<int:id_cliente>', methods=['PATCH'])
def alterar_status_cliente(id_cliente):
    try:
        cliente = db_session.query(Cliente).filter(Cliente.id_cliente == id_cliente).first()

        if not cliente:
            return jsonify({"mensagem": "Cliente não encontrado"}), 404

        # Inverte o status
        cliente.ativo = not cliente.ativo

        db_session.commit()
        return jsonify({"mensagem": "Status do cliente alterado com sucesso", "ativo": cliente.ativo}), 200

    except Exception as e:
        print(f"Erro ao alterar status do cliente: {e}")
        return jsonify({"mensagem": "Erro interno do servidor"}), 500

@app.route('/adicionarClientes', methods=['POST'])
def adicionar_cliente():
    try:
        dados_cliente = request.get_json()

        campos_obrigatorios = ["nome", "cpf", "telefone", "endereco"]
        for campo in campos_obrigatorios:
            if campo not in dados_cliente or not dados_cliente[campo].strip():
                return jsonify({"mensagem": f"Campo '{campo}' é obrigatório e não pode estar vazio."}), 400

        cpf = dados_cliente['cpf']
        telefone = dados_cliente['telefone']

        # Verificar se o CPF já existe
        cpf_existente = db_session.execute(select(Cliente).where(Cliente.cpf == cpf)).scalar()
        if cpf_existente:
            return jsonify({"mensagem": "CPF já cadastrado"}), 409

        # Verificar se o telefone já existe
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
@jwt_required()
def listar_clientes():
    try:
        lista_clientes = db_session.query(Cliente).all()
        resultado = [cliente.serialize() for cliente in lista_clientes]
        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro ao listar clientes: {e}")
        return jsonify({"mensagem": "Erro ao obter clientes"}), 500

@app.route("/editarClients/<int:cliente_id>", methods=['PUT'])
def editar_clientes(cliente_id):
    cliente = db_session.execute(
        select(Cliente).where(Cliente.id_cliente == cliente_id)
    ).scalar()

    if cliente is None:
        return jsonify({"mensagem": "Cliente não encontrado"}), 404

    dados_cliente = request.get_json()
    print("Dados recebidos:", dados_cliente)  # DEBUG

    cliente.nome = dados_cliente['nome']
    cliente.cpf = dados_cliente['cpf']
    cliente.telefone = dados_cliente['telefone']
    cliente.endereco = dados_cliente['endereco']

    db_session.commit()  # em vez de cliente.save()
    return jsonify({"mensagem": "cliente editado com sucesso"}), 200

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
    try:

        dados_veiculo = request.get_json()
        campos_obrigatorios = ["cliente_id", "marca", "modelo", "placa", "ano_fabricacao"]
        for campo in campos_obrigatorios:
            if campo not in dados_veiculo or not dados_veiculo[campo].strip():
                return jsonify({"mensagem": f"Campo '{campo}' é obrigatório e não pode estar vazio."}), 400
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
@jwt_required()
def listar_veiculos():
    try:
        lista_veiculos = db_session.query(Veiculo).all()
        resultado = [veiculo.serialize() for veiculo in lista_veiculos]
        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro ao listar veículos: {e}")
        return jsonify({"mensagem": "Erro ao obter veículos"}), 500


@app.route("/editarVeiculos/<int:id_veiculo>", methods=['PUT'])
def editar_veiculos(id_veiculo):
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
def deletar_veiculo(id_veiculo):
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
    try:
        dados_ordem = request.get_json()

        # Converte string para objeto datetime
        try:
            data_abertura = datetime.strptime(dados_ordem['data_abertura'], "%Y-%m-%d")
        except ValueError:
            return jsonify({"mensagem": "Formato de data inválido. Use AAAA-MM-DD"}), 400

        nova_ordem = OrdemServico(
            veiculo_id=int(dados_ordem['veiculo_id']),
            data_abertura=data_abertura,
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
@jwt_required()
def listar_ordem_servicos():
    try:
        lista_ordens = db_session.query(OrdemServico).all()
        resultado = [ordem.serialize() for ordem in lista_ordens]
        return jsonify(resultado), 200
    except Exception as e:
        print(f"Erro ao listar ordens de serviço: {e}")
        return jsonify({"mensagem": "Erro ao obter ordens de serviço"}), 500


@app.route("/editarServico/<int:id_servico>", methods=['PUT'])
def editar_servico(id_servico):
    # Busca a ordem de serviço pelo id
    ordens_servico = db_session.execute(
        select(OrdemServico).where(OrdemServico.id_servico == id_servico)
    ).scalar()

    if ordens_servico is None:
        return jsonify({"mensagem": "Serviço não encontrado"}), 404

    dados_ordem = request.get_json()

    try:
        data_str = dados_ordem.get('data_abertura', '').strip()
        if data_str:
            data_str = data_str.split("T")[0]
            ordens_servico.data_abertura = datetime.strptime(data_str, "%Y-%m-%d").date()
        else:
            ordens_servico.data_abertura = None

        ordens_servico.descricao_servico = dados_ordem['descricao_servico']
        ordens_servico.status = dados_ordem['status']
        ordens_servico.valor_estimado = float(dados_ordem['valor_estimado'])

        if ordens_servico.status.lower() in ["concluído", "finalizado"]:
            ordens_servico.data_fechamento = datetime.utcnow()

        ordens_servico.save()
        return jsonify({"mensagem": "Serviço editado com sucesso"}), 200

    except (KeyError, ValueError, TypeError) as err:
        print(f"Erro ao editar serviço: {err}")
        return jsonify({"mensagem": "Erro nos dados enviados"}), 400
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
