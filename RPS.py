import random
from collections import Counter

# --- Constantes y variables globales ---
moves_list = ["R", "P", "S"]
ideal_response = {'P': 'S', 'R': 'P', 'S': 'R'}

# Historiales globales (se usan listas para mantener la secuencia)
my_history = []           # Nuestras jugadas
opponent_history_global = []   # Jugadas del oponente
name_history = []         # Historial del nombre del bot detectado

# Diccionario para mapear el código de las primeras jugadas a un bot
codetobot = {
    "RPP": "quincy",
    "PPP": "abbey",
    "PPS": "kris",
    "RRR": "mrugesh"
}

# --- Función de contrarresto ---
def countering_moves(move):
    if move == "R":
        return "P"
    if move == "P":
        return "S"
    if move == "S":
        return "R"
    return random.choice(moves_list)

# --- Predictores (Expertos) del meta-algoritmo ---
def predictor_last(opp_history):
    return opp_history[-1] if opp_history else "R"

def predictor_freq(opp_history):
    if not opp_history:
        return "R"
    freq = Counter(opp_history)
    return freq.most_common(1)[0][0]

def predictor_markov(opp_history):
    if len(opp_history) < 4:
        return predictor_last(opp_history)
    last3 = ''.join(opp_history[-3:])
    candidates = []
    for i in range(len(opp_history) - 3):
        if ''.join(opp_history[i:i+3]) == last3:
            candidates.append(opp_history[i+3])
    if candidates:
        return Counter(candidates).most_common(1)[0][0]
    else:
        return predictor_last(opp_history)

def predictor_pattern(opp_history):
    n = len(opp_history)
    for length in range(n-1, 0, -1):
        suffix = opp_history[-length:]
        for i in range(n - length):
            if opp_history[i:i+length] == suffix:
                if i+length < n:
                    return opp_history[i+length]
    return predictor_last(opp_history)

def predictor_random(opp_history):
    return random.choice(moves_list)

def predictor_abbey(opp_history):
    if len(opp_history) < 2:
        return predictor_last(opp_history)
    play_order = {"RR": 0, "RP": 0, "RS": 0,
                  "PR": 0, "PP": 0, "PS": 0,
                  "SR": 0, "SP": 0, "SS": 0}
    for i in range(len(opp_history)-1):
        pair = ''.join(opp_history[i:i+2])
        if pair in play_order:
            play_order[pair] += 1
    potential = [opp_history[-1] + "R", opp_history[-1] + "P", opp_history[-1] + "S"]
    sub_order = {p: play_order[p] for p in potential}
    if sub_order:
        prediction = max(sub_order, key=sub_order.get)
        return prediction[-1]
    return predictor_last(opp_history)

candidate_functions = {
    "last": predictor_last,
    "freq": predictor_freq,
    "markov": predictor_markov,
    "pattern": predictor_pattern,
    "random": predictor_random,
    "abbey": predictor_abbey
}
candidate_names = list(candidate_functions.keys())

# Boost factors para cada experto
boost_factors = {
    "abbey": 1.5,
    "last": 1.0,
    "freq": 1.0,
    "markov": 1.0,
    "pattern": 1.0,
    "random": 1.0
}

DECAY = 0.99  # Factor de decaimiento

# Variables para el meta-algoritmo (se usan listas/diccionarios globales)
candidate_scores = {}        # Se inicializará al inicio de cada match
candidate_predictions = {}

# --- Función Outcome ---
def outcome(our_move, opp_move):
    if (our_move == "R" and opp_move == "S") or \
       (our_move == "P" and opp_move == "R") or \
       (our_move == "S" and opp_move == "P"):
        return 1
    elif our_move == opp_move:
        return 0
    else:
        return -1

# --- Estrategia determinista para abbey ---
def deterministic_abbey_strategy():
    """
    Si se detecta abbey, utiliza la jugada que se jugó dos rondas atrás y contraataca con la respuesta ideal.
    """
    if len(my_history) >= 2:
        base_move = my_history[-2]
        return ideal_response[base_move]
    else:
        return "R"

# --- Función para detectar abbey ---
def detect_abbey(opponent_history):
    """
    Detecta si el oponente responde como abbey.
    Ejemplo: si en las primeras 5 jugadas el oponente juega mayoritariamente "P".
    """
    if len(opponent_history) < 5:
        return False
    code = "".join(opponent_history[:5])
    if code.count("P") >= 4:
        return True
    return False

# --- Función player principal ---
def player(prev_play="", opponent_history_local=[]):
    """
    Combina una estrategia determinista para abbey y el meta-algoritmo para otros bots.
    - En las primeras 3 rondas se usa un patrón fijo ("R", "P", "S") para codificar.
    - En la ronda 4 se forma un código y se detecta el bot mediante 'codetobot'.
    - Si se detecta abbey, se utiliza la estrategia determinista.
    - Si no, se usa el meta-algoritmo de expertos.
    """
    global my_history, opponent_history_global, name_history
    global candidate_scores, candidate_predictions

    # Actualizar el historial local del oponente
    opponent_history_local.append(prev_play)
    round_number = len(opponent_history_local)

    # Reinicio periódico (por ejemplo, cada 1000 rondas)
    if round_number == 1001:
        opponent_history_local.clear()
        opponent_history_local.append(prev_play)
        name_history.clear()
        name_history.append('')
        my_history.clear()

    # Fase de Apertura: las primeras 3 rondas se usan para codificar.
    if round_number <= 3:
        pattern = ["R", "P", "S"]
        move = pattern[round_number - 1]
        my_history.append(move)
        return move

    # Ronda 4: determinar el bot usando un código formado por las jugadas 2 a 4 del oponente.
    if round_number == 4:
        opp_code = "".join(opponent_history_local[1:4])
        detected_bot = codetobot.get(opp_code, "unknown")
        name_history.append(detected_bot)

    # Si se ha detectado abbey, usar la estrategia determinista.
    if name_history and name_history[-1] == "abbey":
        guess = deterministic_abbey_strategy()
        my_history.append(guess)
        return guess

    # Para otros bots, usar el meta-algoritmo de expertos.

    # Asegurarse de que candidate_scores y candidate_predictions estén inicializados
    if not candidate_scores:
        candidate_scores = {name: 0 for name in candidate_names}
        candidate_predictions = {}

    # Actualizar puntajes en base a la predicción de la ronda anterior (si existen)
    if candidate_predictions:
        for name, pred in candidate_predictions.items():
            candidate_move = countering_moves(pred)
            res = outcome(candidate_move, prev_play)
            update = (2 * res) if res < 0 else res
            boost = boost_factors.get(name, 1.0)
            update *= boost
            candidate_scores[name] = candidate_scores.get(name, 0) * DECAY + update

    # Calcular las predicciones actuales de cada experto
    candidate_predictions = {}
    for name in candidate_names:
        func = candidate_functions[name]
        candidate_predictions[name] = func(opponent_history_local)

    # Seleccionar el experto con mayor puntaje (desempate aleatorio)
    max_score = max(candidate_scores.values())
    best_experts = [n for n, s in candidate_scores.items() if s == max_score]
    chosen_expert = random.choice(best_experts)
    predicted_move = candidate_predictions[chosen_expert]

    # La jugada final es contraatacar la predicción elegida.
    final_move = countering_moves(predicted_move)
    my_history.append(final_move)
    return final_move
