# -*- coding: utf-8 -*-
'''
Esse projeto é um exemplo inicial de como usar Flask + SQLite.

O exemplo tem muitos pontos de melhoria que não foram explorados uma vez que o foco está em mostrar os conceitos fundamentais.

https://www.pythonsheets.com/notes/python-sqlalchemy.html

https://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html

Emerson Ribeiro de Mello - 2018
'''
from flask import (
    redirect, render_template, request, session, url_for, Flask
)

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

# Chave usada para cifrar dados da sessão do usuário (e cookies) e assim evitar alguns tipos de ataque
# Deve ser escolhido um valor que não possa ser deduzido facilmente, até mesmo por força bruta. Nunca pode ser revelado para terceiros
SECRET_KEY = 'aula de BCD - string aleatória'


app = Flask(__name__)
app.secret_key = SECRET_KEY

# Fazendo  Mapeamento objeto relacional (Object Relational Mapper - ORM) com engenharia reversa - refletion
engine = create_engine("sqlite:///lab05.sqlite")
Session = sessionmaker(bind=engine)
Base = automap_base()
Base.prepare(engine, reflect=True)

# Tabelas existentes no SQLite
Pessoa = Base.classes.Pessoa
Telefones = Base.classes.Telefones


@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/listar')
def listar_pessoas():
    sessionSQL = Session()
    # Listando todas pessoas
    pessoas = sessionSQL.query(Pessoa).all()
    sessionSQL.close()
    return render_template('listar.html', title='Listar', pessoas=pessoas)



@app.route('/editar', methods=['GET', 'POST'])
def editar():
    sessionSQL = Session()
    if request.method == 'GET':
        # pegar o id da pessoa via GET (parâmetro id na URL)
        pessoaId = str(request.args.get('id'))

        pessoa = sessionSQL.query(Pessoa).filter(Pessoa.idPessoa == pessoaId).first()

        if pessoa is None:
            return redirect(url_for('listar_pessoas'))

        telefones = sessionSQL.query(Telefones).filter(Telefones.idPessoa == pessoaId).all()

        # adicionando id da pessoa na sessão do usuário
        session['pessoaId'] = pessoaId
        telIds = []
        for tel in telefones:
            telIds.append(tel.idTelefone)
        # adicionando id dos telefones da pessoa na sessão
        session['telefones'] = telIds
        return render_template('editar.html', title='Editar pessoa', pessoa=pessoa)
    else:
        # obtendo ids que estavam na sessão
        pessoaId = session['pessoaId']
        telefones = session['telefones']
        # limpando a sessão
        session.pop('pessoaId', None)
        session.pop('telefones', None)

        # obtendo o novo valor que estava no campo 'nome' do formulário da página editar.html
        nome = request.form['nome']

        # buscando pela pessoa
        pessoa = sessionSQL.query(Pessoa).filter(Pessoa.idPessoa == pessoaId).first()

        # atualizando o nome da pessoa
        pessoa.nome = nome

        # atualizando os telefones da pessoa
        for campo in request.form.items():
            # o nome do campo no formulário está no formato: tele-IDTELEFONE
            if 'tele-' in campo[0]:
                # pegando somente o IDTELEFONE e descartando o tele-
                idTelefone = campo[0].split('-')[1]
                if (int(idTelefone)) in telefones:
                    for tel in pessoa.telefones_collection:
                        if tel.idTelefone == int(idTelefone):
                            tel.numero = campo[1]
                            continue

        # persistindo os dados
        sessionSQL.commit()
        sessionSQL.close()
        return redirect(url_for('listar_pessoas'))

@app.route('/excluir', methods=['GET', 'POST'])
def excluir():
    sessionSQL = Session()
    if request.method == 'GET':
        # pegar o id da pessoa via GET (parâmetro id na URL)
        pessoaId = str(request.args.get('id'))
        pessoa = sessionSQL.query(Pessoa).filter(Pessoa.idPessoa == pessoaId).first()

        if pessoa is None:
            return redirect(url_for('listar_pessoas'))

        # adicionando id da pessoa na sessão do usuário
        session['pessoaId'] = pessoaId
        return render_template('excluir.html', title='Excluir pessoa', pessoa=pessoa)
    else:
        # obtendo ids que estavam na sessão
        pessoaId = session['pessoaId']
        # limpando a sessão
        session.pop('pessoaId', None)
        # buscando pela pessoa
        pessoa = sessionSQL.query(Pessoa).filter(Pessoa.idPessoa == pessoaId).first()

        # excluindo seus telefones
        pessoa.telefones_collection[:] = [] # limpando a lista vai refletir diretamente no DB
        # excluindo a pessoa
        sessionSQL.delete(pessoa)

        # leia mais detalhes em https://docs.sqlalchemy.org/en/latest/orm/cascades.html
        # ORM-level “delete” cascade vs. FOREIGN KEY level “ON DELETE” cascade

        sessionSQL.commit()
        sessionSQL.close()
        return redirect(url_for('listar_pessoas'))


@app.route('/inserir', methods=['GET', 'POST'])
def inserir():
    if request.method == 'GET':
        return render_template('inserir.html', title='Adicionar pessoa')
    else:
        sessionSQL = Session()

        # obtendo o novo valor que estava no campo 'nome' do formulário da página editar.html
        nome = request.form['nome']

        pessoa = Pessoa()
        pessoa.nome = nome

        # Criando um telefone estaticamente para uma nova pessoa
        tel = Telefones()
        tel.numero = '(48) 3210-1234'
        pessoa.telefones_collection.append(tel)

        sessionSQL.add(pessoa)
        sessionSQL.commit()
        sessionSQL.close()

        return redirect(url_for('listar_pessoas'))


if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True)
