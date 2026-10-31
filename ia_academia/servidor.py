import os
from flask import Flask, request, jsonify, send_from_directory
from assistente import responder, risco_de_desistir

app = Flask(__name__)


def limpar_aluno(dados):
    """Converte os campos numéricos e garante que nada falte."""
    try:
        return {
            "idade": int(dados["idade"]),
            "objetivo": str(dados["objetivo"]),
            "nivel": str(dados["nivel"]),
            "frequencia_semanal": int(dados["frequencia_semanal"]),
            "meses_matricula": int(dados["meses_matricula"]),
            "faltas_ultimo_mes": int(dados["faltas_ultimo_mes"]),
        }
    except (KeyError, ValueError, TypeError):
        return None


@app.get("/health")
def health():
    return jsonify({"status": "ok", "mensagem": "Servidor Flask está funcionando"})


@app.get("/")
def pagina_inicial():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    public_dir = os.path.join(project_root, "public")
    return send_from_directory(public_dir, "index.html")


@app.post("/api/risco")
def api_risco():
    corpo = request.get_json(silent=True) or {}
    aluno = limpar_aluno(corpo.get("aluno", {}))
    if aluno is None:
        return jsonify({"erro": "Dados do aluno inválidos"}), 400
    return jsonify({"risco": float(risco_de_desistir(aluno))})


@app.post("/api/chat")
def api_chat():
    corpo = request.get_json(silent=True) or {}
    aluno = limpar_aluno(corpo.get("aluno", {}))
    historico = corpo.get("historico", [])
    if aluno is None or not historico:
        return jsonify({"erro": "Dados inválidos"}), 400
    try:
        resposta = responder(aluno, historico)
        return jsonify({"resposta": resposta, "risco": float(risco_de_desistir(aluno))})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
