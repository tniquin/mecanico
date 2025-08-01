from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, DateTime, Enum, func, Boolean
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
##
engine = create_engine('sqlite:///mecanica.db')
db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    cpf = Column(String(11), nullable=False, unique=True)
    password = Column(String, nullable=False)
    papel = Column(String)


    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<Usuario(id={self.id}, nome={self.nome}, email={self.email}, cpf={self.cpf}, papel={self.papel})>'

    def serialize(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "email": self.email,
            "papel": self.papel,
        }

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()



class Cliente(Base):
    __tablename__ = 'clientes'
    id_cliente = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    cpf = Column(String(11), unique=True, nullable=False)
    telefone = Column(String(20), nullable=False)
    endereco = Column(String(200), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    ativo = Column(Boolean, default=True)
    veiculos = relationship('Veiculo', backref='proprietario', lazy=True)

    def __repr__(self):
        return f'<Cliente(id={self.id_cliente}, email={self.email}, nome={self.nome}, cpf={self.cpf}, endereco={self.endereco})>'

    def serialize(self):
        return {
            "id_cliente": self.id_cliente,
            "nome": self.nome,
            "cpf": self.cpf,
            "telefone": self.telefone,
            "endereco": self.endereco,
            "email": self.email,
            "ativo": self.ativo,
            "motivo_inativo": getattr(self, "motivo_inativo", None),
        }

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()


class Veiculo(Base):
    __tablename__ = 'veiculos'
    id_veiculo = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id_cliente'), nullable=False)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    placa = Column(String(10), unique=True, nullable=False)
    ano_fabricacao = Column(Integer, nullable=False)
    ordens_servico = relationship('OrdemServico', back_populates='veiculo', lazy=True)


    def __repr__(self):
        return f'<Veiculo(id={self.id_veiculo}, placa={self.placa}, modelo={self.modelo})>'

    def serialize(self):
        return {
            "id_veiculo": self.id_veiculo,
            "cliente_id": self.cliente_id,
            "marca": self.marca,
            "modelo": self.modelo,
            "placa": self.placa,
            "ano_fabricacao": self.ano_fabricacao,
        }

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

class OrdemServico(Base):
    __tablename__ = 'ordem_servico'

    id_servico = Column(Integer, primary_key=True)
    veiculo_id = Column(Integer, ForeignKey('veiculos.id_veiculo'))
    data_abertura = Column(DateTime, default=datetime.utcnow)
    descricao_servico = Column(String(200))
    status = Column(String(50))
    valor_estimado = Column(Float)
    data_fechamento = Column(DateTime, nullable=True)

    veiculo = relationship("Veiculo", back_populates="ordens_servico")

    def serialize(self):
        return {
            "id_servico": self.id_servico,
            "veiculo_id": self.veiculo_id,
            "data_abertura": self.data_abertura.strftime("%d-%m-%Y %H:%M") if self.data_abertura else None,
            "descricao_servico": self.descricao_servico,
            "status": self.status,
            "valor_estimado": self.valor_estimado,
            "data_fechamento": self.data_fechamento.strftime("%d-%m-%Y %H:%M") if self.data_fechamento else None

        }

    def save(self):
        db_session.add(self)
        db_session.commit()

    def delete(self):
        db_session.delete(self)
        db_session.commit()

def init_db():
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    init_db()