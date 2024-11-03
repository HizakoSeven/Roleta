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

# Funções de carregamento e salvamento de dados permanecem as mesmas

# Carregar os dados existentes
counters = load_data(data_file_path)
limited_counters = load_data(limited_data_file_path)
record = load_data(record_file_path)

# Variáveis para controle de reset diário por canal
last_reset_date = {}
last_limited_reset_date = {}

# Funções de reset diário permanecem as mesmas

# Função para atualizar o recorde permanece a mesma

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
        record_broken = update_record(channel, user, user_streak)

        counters[channel][user] = 0  # Resetar o contador do usuário
        save_data(counters, data_file_path)

        # Mensagem de notificação
        if record_broken:
            notification = f'💥 {user}, você tomou o tiro e QUEBROU O RECORDE com {user_streak} sobrevivências! Seu contador foi resetado.'
        else:
            notification = f'💥 {user}, você tomou o tiro! Seu contador foi resetado.'

        # Retornar o JSON com o indicador de timeout
        return json.dumps({
            'message': notification,
            'timeout': True,
            'user': user
        })

    else:
        counters[channel][user] = counters[channel].get(user, 0) + 1  # Incrementar o contador
        save_data(counters, data_file_path)

        # Verificar se o usuário quebrou o recorde
        user_streak = counters[channel][user]
        record_broken = update_record(channel, user, user_streak)

        if record_broken:
            notification = f'🎉 {user}, você sobreviveu e QUEBROU O RECORDE com {user_streak} sobrevivências consecutivas!'
        else:
            notification = f':) {user}, você sobreviveu! Tentativas sem tomar o tiro: {user_streak}.'

        return json.dumps({
            'message': notification,
            'timeout': False
        })

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
        return json.dumps({
            'message': f'🚫 {user}, você já levou 3 tiros hoje. Volte em 24 horas.',
            'timeout': False
        })

    # Gerar um número aleatório de 1 a 6
    tiro = randint(1, 6)

    if tiro == 1:
        # Verificar se o usuário quebrou o recorde antes de tomar o tiro
        user_streak = user_data.get('streak', 0)
        record_broken = update_record(channel, user, user_streak)

        user_data['shotsTaken'] += 1  # Incrementar o número de tiros tomados
        user_data['streak'] = 0  # Resetar a sequência de sobrevivências
        limited_counters[channel][user] = user_data
        save_data(limited_counters, limited_data_file_path)

        # Mensagem de notificação
        if record_broken:
            if user_data['shotsTaken'] >= 3:
                notification = f'💥 {user}, você tomou o tiro, atingiu o limite de 3 tiros e QUEBROU O RECORDE com {user_streak} sobrevivências! Volte amanhã para jogar novamente.'
            else:
                notification = f'💥 {user}, você tomou o tiro e QUEBROU O RECORDE com {user_streak} sobrevivências! {user_data["shotsTaken"]}/3.'
        else:
            if user_data['shotsTaken'] >= 3:
                notification = f'💥 {user}, você tomou o tiro e atingiu o limite de 3 tiros hoje. Volte amanhã.'
            else:
                notification = f'💥 {user}, você tomou o tiro! {user_data["shotsTaken"]}/3.'

        # Retornar o JSON com o indicador de timeout
        return json.dumps({
            'message': notification,
            'timeout': True,
            'user': user
        })

    else:
        user_data['streak'] = user_data.get('streak', 0) + 1  # Incrementar a sequência de sobrevivências
        limited_counters[channel][user] = user_data
        save_data(limited_counters, limited_data_file_path)

        # Verificar se o usuário quebrou o recorde
        user_streak = user_data['streak']
        record_broken = update_record(channel, user, user_streak)

        if record_broken:
            notification = f'🎉 {user}, você sobreviveu e QUEBROU O RECORDE com {user_streak} sobrevivências consecutivas!'
        else:
            notification = f':) {user}, você sobreviveu! Tentativas sem tomar o tiro: {user_streak}.'

        return json.dumps({
            'message': notification,
            'timeout': False
        })

# Rota '/roletaRecorde' permanece inalterada

# Iniciar o servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
