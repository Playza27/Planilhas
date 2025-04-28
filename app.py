import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Permitir requisições do frontend
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def comparar_planilhas(arquivo1_path, arquivo2_path, colunas_comparar):
    try:
        if len(colunas_comparar) > 10:
            return {"error": "O número máximo de colunas para comparação é 10."}
        if len(colunas_comparar) == 0:
            return {"error": "Nenhuma coluna especificada para comparação."}

        df1 = pd.read_excel(arquivo1_path)
        df2 = pd.read_excel(arquivo2_path)

        for col in colunas_comparar:
            if col not in df1.columns or col not in df2.columns:
                return {"error": f"A coluna '{col}' não existe em uma ou ambas as planilhas."}

        df1 = df1[colunas_comparar]
        df2 = df2[colunas_comparar]

        if df1.shape != df2.shape:
            return {"error": f"Dimensões diferentes! Planilha 1: {df1.shape}, Planilha 2: {df2.shape}"}

        comparacao = df1.eq(df2)
        todas_iguais = comparacao.all().all()

        if todas_iguais:
            return {"status": "success", "message": "As planilhas são idênticas nas colunas especificadas!"}

        resultado = []
        for col in colunas_comparar:
            diff_mask = ~comparacao[col]
            if diff_mask.any():
                diffs = []
                for idx in df1[diff_mask].index:
                    valor1 = df1.loc[idx, col]
                    valor2 = df2.loc[idx, col]
                    diffs.append({
                        "linha": idx + 2,
                        "valor_planilha1": str(valor1),
                        "valor_planilha2": str(valor2)
                    })
                resultado.append({"coluna": col, "diferencas": diffs})

        return {"status": "success", "diferencas": resultado}

    except Exception as e:
        return {"error": str(e)}

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({"error": "Ambos os arquivos devem ser enviados."}), 400

    file1 = request.files['file1']
    file2 = request.files['file2']
    colunas = request.form.getlist('colunas')

    if file1.filename == '' or file2.filename == '':
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    file1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file1.filename))
    file2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file2.filename))

    file1.save(file1_path)
    file2.save(file2_path)

    resultado = comparar_planilhas(file1_path, file2_path, colunas)

    os.remove(file1_path)
    os.remove(file2_path)

    return jsonify(resultado)

@app.route('/get_columns', methods=['POST'])
def get_columns():
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({"error": "Ambos os arquivos devem ser enviados."}), 400

    file1 = request.files['file1']
    file2 = request.files['file2']

    file1_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file1.filename))
    file2_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file2.filename))

    file1.save(file1_path)
    file2.save(file2_path)

    try:
        df1 = pd.read_excel(file1_path)
        df2 = pd.read_excel(file2_path)
        colunas1 = df1.columns.tolist()
        colunas2 = df2.columns.tolist()
        colunas_comuns = list(set(colunas1) & set(colunas2))

        os.remove(file1_path)
        os.remove(file2_path)

        return jsonify({"status": "success", "colunas": colunas_comuns})
    except Exception as e:
        os.remove(file1_path)
        os.remove(file2_path)
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)