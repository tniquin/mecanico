from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, func
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///mecanica.db')
db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


class Cliente(Base):
    __tablename__ = 'clientes'
    id_cliente = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    telefone = Column(String(20), nullable=False)
    endereco = Column(String(200), nullable=False)
    veiculos = relationship('Veiculo', backref='proprietario', lazy=True)

    def __repr__(self):
        return f'<Cliente(id={self.id_cliente}, nome={self.nome}, cpf={self.cpf})>'

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize(self):
        return {
            "id_cliente": self.id_cliente,
            "nome": self.nome,
            "cpf": self.cpf,
            "telefone": self.telefone,
            "endereco": self.endereco,
        }


class Veiculo(Base):
    __tablename__ = 'veiculos'
    id_veiculo = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id_cliente'), nullable=False)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    placa = Column(String(10), unique=True, nullable=False)
    ano_fabricacao = Column(Integer, nullable=False)
    ordens_servico = relationship('OrdemServico', backref='veiculo', lazy=True)

    def __repr__(self):
        return f'<Veiculo(id={self.id_veiculo}, placa={self.placa}, modelo={self.modelo})>'

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize(self):
        return {
            "id_veiculo": self.id_veiculo,
            "cliente_id": self.cliente_id,
            "marca": self.marca,
            "modelo": self.modelo,
            "placa": self.placa,
            "ano_fabricacao": self.ano_fabricacao,
        }



class OrdemServico(Base):
    __tablename__ = 'ordens_servico'
    id_servico = Column(Integer, primary_key=True)
    veiculo_id = Column(Integer, ForeignKey('veiculos.id_veiculo'), nullable=False)
    data_abertura = Column(String(10), nullable=False)
    descricao_servico = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False)
    valor_estimado = Column(Float, nullable=False)

    def __repr__(self):
        return f'<OrdemServico(id={self.id_servico}, veiculo_id={self.veiculo_id}, status={self.status})>'

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

    def serialize(self):
        return {
            "id_servico": self.id_servico,
            "veiculo_id": self.veiculo_id,
            "data_abertura": self.data_abertura,
            "descricao_servico": self.descricao_servico,
            "status": self.status,
            "valor_estimado": self.valor_estimado,
        }



def init_db():
    Base.metadata.create_all(engine)



if __name__ == '__main__':
    init_db()
