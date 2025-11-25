import re
from tabulate import tabulate
import os

BIG_M = 1000000

def obter_proximo_arquivo_resultado():
    """Encontra o próximo nome de arquivo disponível (resultado1.txt, resultado2.txt, etc.)"""
    contador = 1
    while True:
        nome_arquivo = f"resultado{contador}.txt"
        if not os.path.exists(nome_arquivo):
            return nome_arquivo
        contador += 1

def ler_arquivo(nome_arquivo):
    with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
        linhas = [linha.strip() for linha in arquivo.readlines()]

    if not linhas:
        raise ValueError("Arquivo vazio")

    linha_fo = linhas[0].strip()
    if not linha_fo.upper().startswith(('MAX', 'MIN')):
        raise ValueError("Primeira linha deve começar com 'MAX' ou 'MIN'")

    sense = linha_fo[:3].upper()
    fo_str = linha_fo[3:].strip()
    coef_fo = extrair_coeficientes(fo_str)
    
    if len(linhas) < 2 or linhas[1] != '':
        raise ValueError("Segunda linha deve estar em branco")
    
    restricoes = []
    idx = 2
    while idx < len(linhas) and linhas[idx] != '':
        linha = linhas[idx]
        match = re.match(r'(.+?)(<=|>=|=)(.+)', linha)
        if match:
            lhs, op, rhs = match.groups()
            coef_restr = extrair_coeficientes(lhs)
            restricoes.append((coef_restr, float(rhs.strip()), op.strip()))
        idx += 1
    
    if idx < len(linhas) and linhas[idx] == '':
        idx += 1
    
    vars_irrestritas = set()
    vars_negativas = set()
    
    while idx < len(linhas):
        linha = linhas[idx].strip()
        if linha == '':
            idx += 1
            continue
        
        match_livre = re.match(r'^(\w+)\s+livre$', linha, re.IGNORECASE)
        if match_livre:
            var_nome = match_livre.group(1)
            var_num = int(re.search(r'\d+', var_nome).group())
            vars_irrestritas.add(var_num)
            idx += 1
            continue
        
        match_dominio = re.match(r'^(\w+)\s*(>=|<=)\s*0$', linha)
        if match_dominio:
            var_nome = match_dominio.group(1)
            relacional = match_dominio.group(2)
            var_num = int(re.search(r'\d+', var_nome).group())
            
            if relacional == '<=':
                vars_negativas.add(var_num)
            
            idx += 1
            continue
        
        idx += 1
    
    if sense == 'MIN':
        coef_fo = [-c for c in coef_fo]
    
    return coef_fo, restricoes, vars_irrestritas, vars_negativas, sense

def extrair_coeficientes(expressao):
    s = expressao.replace(' ', '')
    s = s.replace('-', '+-')
    if s.startswith('+'):
        s = s[1:]

    matches = re.findall(r'([+-]?)(\d*\.?\d*)[xX](\d+)', s)
    if not matches:
        return []

    max_var = max(int(m[2]) for m in matches)
    coefs = [0.0] * max_var
    
    for sinal, coef, var in matches:
        val = 1.0 if coef in ('', '.') else float(coef)
        if sinal == '-':
            val = -val
        coefs[int(var)-1] = val
    
    return coefs

def expandir_irrestritas(coef_fo, restricoes, vars_irrestritas, vars_negativas):
    if vars_negativas:
        num_x = len(coef_fo)
        for var_idx in vars_negativas:
            if var_idx <= num_x:
                coef_fo[var_idx-1] = -coef_fo[var_idx-1]
                for i in range(len(restricoes)):
                    coef_restr, rhs, op = restricoes[i]
                    if var_idx-1 < len(coef_restr):
                        coef_restr[var_idx-1] = -coef_restr[var_idx-1]
    
    if not vars_irrestritas:
        return coef_fo, restricoes
    
    num_x = len(coef_fo)
    nova_fo = []
    
    for i in range(num_x):
        if (i+1) in vars_irrestritas:
            nova_fo.append(coef_fo[i])
            nova_fo.append(-coef_fo[i])
        else:
            nova_fo.append(coef_fo[i])
    
    novas_restricoes = []
    for coef_restr, rhs, op in restricoes:
        nova_linha = []
        for i in range(num_x):
            c = coef_restr[i] if i < len(coef_restr) else 0.0
            if (i+1) in vars_irrestritas:
                nova_linha.append(c)
                nova_linha.append(-c)
            else:
                nova_linha.append(c)
        novas_restricoes.append((nova_linha, rhs, op))
    
    return nova_fo, novas_restricoes

def montar_tableau(coef_fo, restricoes, vars_irrestritas, vars_negativas):
    coef_fo, restricoes = expandir_irrestritas(coef_fo, restricoes, vars_irrestritas, vars_negativas)
    
    num_x = len(coef_fo)
    num_r = len(restricoes)
    
    A = []
    b = []
    var_names = [f"x{i+1}" for i in range(num_x)]
    basic_vars = []
    
    for coef_restr, rhs, op in restricoes:
        linha = coef_restr.copy()
        while len(linha) < num_x:
            linha.append(0.0)
        A.append(linha)
        b.append(rhs)
    
    for i in range(num_r):
        op = restricoes[i][2]
        
        if op == '<=':
            var_names.append(f"f{i+1}")
            for j in range(num_r):
                A[j].append(1.0 if j == i else 0.0)
            basic_vars.append(len(var_names) - 1)
            
        elif op == '>=':
            var_names.append(f"e{i+1}")
            for j in range(num_r):
                A[j].append(-1.0 if j == i else 0.0)
                
            var_names.append(f"a{i+1}")
            for j in range(num_r):
                A[j].append(1.0 if j == i else 0.0)
            basic_vars.append(len(var_names) - 1)
            
        elif op == '=':
            var_names.append(f"a{i+1}")
            for j in range(num_r):
                A[j].append(1.0 if j == i else 0.0)
            basic_vars.append(len(var_names) - 1)
    
    c = coef_fo + [0.0] * (len(var_names) - num_x)
    for i, name in enumerate(var_names):
        if name.startswith('a'):
            c[i] = -BIG_M
    
    return A, b, var_names, c, basic_vars

def produto_escalar(vec1, vec2):
    """Calcula produto escalar entre dois vetores"""
    return sum(v1 * v2 for v1, v2 in zip(vec1, vec2))

def transpor_matriz(matriz):
    """Transpõe uma matriz (troca linhas por colunas)"""
    if not matriz:
        return []
    return [[matriz[i][j] for i in range(len(matriz))] for j in range(len(matriz[0]))]

def formatar(val):
    if abs(val) > 1000:
        return f"{val:.0f}"
    if abs(val - round(val)) < 1e-10:
        return int(round(val))
    return round(val, 2)

def imprimir(A, b, var_names, c, basic_vars, it=0, arquivo_saida=None):
    m = len(A)
    n = len(A[0]) if A else 0
    
    c_B = [c[basic_vars[i]] for i in range(m)]
    
    A_T = transpor_matriz(A)
    
    c_B_A = [produto_escalar(c_B, coluna) for coluna in A_T]
    z = [-c[j] + c_B_A[j] for j in range(n)]
    
    z_b = produto_escalar(c_B, b)
    
    headers = ["VB", "-Z"] + var_names + ["b"]
    dados = []
    
    for i in range(m):
        linha = [var_names[basic_vars[i]], 0]
        linha += [formatar(A[i][j]) for j in range(n)]
        linha += [formatar(b[i])]
        dados.append(linha)
    
    linha_z = ["-Z", 1] + [formatar(z[j]) for j in range(n)] + [formatar(z_b)]
    dados.append(linha_z)
    
    output = "\n" + "="*80 + "\n"
    output += f"ITERACAO {it}\n"
    output += "="*80 + "\n"
    output += tabulate(dados, headers=headers, tablefmt="grid")
    
    print(output)
    
    if arquivo_saida:
        with open(arquivo_saida, 'a', encoding='utf-8') as f:
            f.write(output + "\n")
    
    return z, z_b

def simplex(A, b, var_names, c, basic_vars, arquivo_saida=None):
    it = 0
    
    while it < 100:
        z, z_b = imprimir(A, b, var_names, c, basic_vars, it, arquivo_saida)
        
        if all(z[j] >= -1e-10 for j in range(len(z))):
            tem_artificial = any(var_names[basic_vars[i]].startswith('a') for i in range(len(basic_vars)))
            resultado = "\nINVIAVEL\n" if tem_artificial else "\nOTIMO\n"
            print(resultado)
            if arquivo_saida:
                with open(arquivo_saida, 'a', encoding='utf-8') as f:
                    f.write(resultado)
            return resultado == "\nOTIMO\n", z_b
        
        col = min(range(len(z)), key=lambda j: z[j])
        
        if all(A[i][col] <= 1e-10 for i in range(len(b))):
            resultado = "\nILIMITADO\n"
            print(resultado)
            if arquivo_saida:
                with open(arquivo_saida, 'a', encoding='utf-8') as f:
                    f.write(resultado)
            return False, None
        
        razoes = []
        for i in range(len(b)):
            if A[i][col] > 1e-10:
                razoes.append((b[i] / A[i][col], i))
            else:
                razoes.append((float('inf'), i))
        
        _, lin = min(razoes)
        
        pivo = A[lin][col]
        
        A[lin] = [A[lin][j] / pivo for j in range(len(A[lin]))]
        b[lin] = b[lin] / pivo
        
        for i in range(len(b)):
            if i != lin:
                fator = A[i][col]
                A[i] = [A[i][j] - fator * A[lin][j] for j in range(len(A[i]))]
                b[i] = b[i] - fator * b[lin]
        
        basic_vars[lin] = col
        it += 1
    
    return False, None

def main():
    arquivo = 'exemplo.txt'
    arquivo_resultado = obter_proximo_arquivo_resultado()
    
    print(f"\nResultados serão salvos em: {arquivo_resultado}\n")
    
    coef_fo, restricoes, vars_irrestritas, vars_negativas, sense = ler_arquivo(arquivo)
    
    num_vars_originais = len(coef_fo)
    
    A, b, var_names, c, basic_vars = montar_tableau(coef_fo, restricoes, vars_irrestritas, vars_negativas)
    
    info_problema = "\nPROBLEMA:\n"
    info_problema += f"Sense: {sense}\n"
    info_problema += f"Variaveis: {num_vars_originais}\n"
    info_problema += f"Restricoes: {len(restricoes)}\n"
    info_problema += f"Variaveis irrestritas: {vars_irrestritas if vars_irrestritas else 'Nenhuma'}\n"
    info_problema += f"Variaveis negativas: {vars_negativas if vars_negativas else 'Nenhuma'}\n"
    
    print(info_problema)
    
    with open(arquivo_resultado, 'w', encoding='utf-8') as f:
        f.write(info_problema)
    
    sucesso, valor_otimo = simplex(A, b, var_names, c, basic_vars, arquivo_resultado)
    
    if sucesso:
        sbf = [0.0] * len(var_names)
        for i, idx in enumerate(basic_vars):
            sbf[idx] = b[i]
        
        solucao = "\n" + "="*80 + "\n"
        solucao += "SOLUCAO OTIMA\n"
        solucao += "="*80 + "\n"
        
        idx_atual = 0
        for i in range(num_vars_originais):
            var_num = i + 1
            
            if var_num in vars_irrestritas:
                valor = sbf[idx_atual] - sbf[idx_atual + 1]
                idx_atual += 2
            else:
                valor = sbf[idx_atual]
                if var_num in vars_negativas:
                    valor = -valor
                idx_atual += 1
            
            solucao += f"x{var_num} = {formatar(valor)}\n"
        
        if sense == 'MIN':
            valor_otimo = -valor_otimo
        
        solucao += f"\nFO = {formatar(valor_otimo)}\n"
        solucao += "="*80 + "\n"
        
        print(solucao)
        
        with open(arquivo_resultado, 'a', encoding='utf-8') as f:
            f.write(solucao)
    
    print(f"\nResultados salvos em: {arquivo_resultado}")

if __name__ == "__main__":
    main()