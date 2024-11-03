from flask import Flask, request
import os
import json
from datetime import datetime
from random import randint

app = Flask(__name__)
port = int(os.environ.get("PORT", 3000))

# Caminhos para os arquivos de dados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_file_path = os.path.join(BASE_DIR, 'counters.json')
limited_data_file_path = os.path.join(BASE_DIR, 'limited_counters.json')
record_file_path = os.path.join(BASE_DIR, 'record.json')

# Função para carregar dados de um arquivo
def load_data(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        print(f"Erro ao carregar dados do arquivo {file_path}: {e}")
        return {}

# Função para salvar dados em um arquivo
def save_data(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar dados no arquivo {file_path}: {e}")

# Carregar os dados existentes
counters = load_data(data_file_path)
limited_counters = load_data(limited_data_file_path)
record = load_data(record_file_path)

# Variáveis para controle de reset diário por canal
last_reset_date = {}
last_limited_reset_date = {}

# Função para verificar e resetar os contadores da roleta normal diariamente
def check_daily_reset(channel):
    current_date = datetime.now().strftime('%Y-%m-%d')
    if last_reset_date.get(channel) != current_date:
        counters[channel] = {}  # Resetar todos os contadores do canal
        last_reset_date[channel] = current_date
        save_data(counters, data_file_path)
        print(f"Contadores da roleta normal resetados para um novo dia no canal {channel}.")

# Função para verificar e resetar os contadores da roleta limitada diariamente
def check_limited_daily_reset(channel):
    current_date = datetime.now().strftime('%Y-%m-%d')
    if last_limited_reset_date.get(channel) != current_date:
        limited_counters[channel] = {}  # Resetar todos os contadores do canal
        last_limited_reset_date[channel] = current_date
        save_data(limited_counters, limited_data_file_path)
        print(f"Contadores da roleta limitada resetados para um novo dia no canal {channel}.")

# Função para atualizar o recorde
def update_record(channel, user, streak):
    if not record.get(channel) or streak > record[channel]['streak']:
        record[channel] = {
            'user': user,
            'streak': streak
        }
        save_data(record, record_file_path)
        return True  # Retorna True se o recorde foi quebrado
    return False  # Retorna False se o recorde não foi quebrado

# Rota raiz para verificar se a API está funcionando
@app.route('/')
def index():
    return 'API da Roleta Russa está funcionando!'

# Rota '/roleta' para a lógica da roleta normal
@app.route('/roleta')
def roleta():
    user = request.args.get('user')
    channel = request.args.get('channel')
    if not user or not channel:
        return 'Usuário ou canal não especificado.'

    # Inicializar as estruturas de dados para o canal, se necessário
    if channel not in counters:
        counters[channel] = {}
    if channel not in last_reset_date:
        last_reset_date[channel] = ''

    check_daily_reset(channel)  # Verificar se precisa resetar os contadores do canal

    # Gerar um número aleatório de 1 a 6
    tiro = randint(1, 6)

    if tiro == 1:
        # Verificar se o usuário quebrou o recorde antes de tomar o tiro
        user_streak = counters[channel].get(user, 0)
        update_record(channel, user, user_streak)

        counters[channel][user] = 0  # Resetar o contador do usuário
        save_data(counters, data_file_path)

        # Retornar apenas o comando de timeout
        return f'/timeout {user} 10'

    else:
        counters[channel][user] = counters[channel].get(user, 0) + 1  # Incrementar o contador
        save_data(counters, data_file_path)

        # Verificar se o usuário quebrou o recorde
        user_streak = counters[channel][user]
        record_broken = update_record(channel, user, user_streak)

        if record_broken:
            return f'🎉 {user}, você sobreviveu e QUEBROU O RECORDE com {user_streak} sobrevivências consecutivas!'
        else:
            return f':) {user}, você sobreviveu! Tentativas sem tomar o tiro: {user_streak}.'

# Rota '/roletaLimitada' para a lógica da roleta limitada
@app.route('/roletaLimitada')
def roleta_limitada():
    user = request.args.get('user')
    channel = request.args.get('channel')
    if not user or not channel:
        return 'Usuário ou canal não especificado.'

    # Inicializar as estruturas de dados para o canal, se necessário
    if channel not in limited_counters:
        limited_counters[channel] = {}
    if channel not in last_limited_reset_date:
        last_limited_reset_date[channel] = ''

    check_limited_daily_reset(channel)  # Verificar se precisa resetar os contadores do canal

    # Verificar quantos tiros o usuário já tomou hoje
    user_data = limited_counters[channel].get(user, {'shotsTaken': 0, 'streak': 0})

    if user_data['shotsTaken'] >= 3:
        return f'🚫 {user}, você já levou 3 tiros hoje. Volte em 24 horas.'

    # Gerar um número aleatório de 1 a 6
    tiro = randint(1, 6)

    if tiro == 1:
        # Verificar se o usuário quebrou o recorde antes de tomar o tiro
        user_streak = user_data.get('streak', 0)
        update_record(channel, user, user_streak)

        user_data['shotsTaken'] += 1  # Incrementar o número de tiros tomados
        user_data['streak'] = 0  # Resetar a sequência de sobrevivências
        limited_counters[channel][user] = user_data
        save_data(limited_counters, limited_data_file_path)

        # Retornar apenas o comando de timeout
        return f'/timeout {user} 10'

    else:
        user_data['streak'] = user_data.get('streak', 0) + 1  # Incrementar a sequência de sobrevivências
        limited_counters[channel][user] = user_data
        save_data(limited_counters, limited_data_file_path)

        # Verificar se o usuário quebrou o recorde
        user_streak = user_data['streak']
        record_broken = update_record(channel, user, user_streak)

        if record_broken:
            return f'🎉 {user}, você sobreviveu e QUEBROU O RECORDE com {user_streak} sobrevivências consecutivas!'
        else:
            return f':) {user}, você sobreviveu! Tentativas sem tomar o tiro: {user_streak}.'

# Rota '/roletaRecorde' para exibir o recorde atual
@app.route('/roletaRecorde')
def roleta_recorde():
    channel = request.args.get('channel')
    if not channel:
        return 'Canal não especificado.'

    if record.get(channel) and record[channel].get('user') and record[channel].get('streak'):
        return f'🏆 O recorde atual no canal é de {record[channel]["user"]}, com {record[channel]["streak"]} sobrevivências consecutivas!'
    else:
        return f'Ainda não há um recorde registrado no canal {channel}. Seja o primeiro a estabelecê-lo!'

# Iniciar o servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
