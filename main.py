import re
import numpy as np
from tabulate import tabulate

BIG_M = 1000000

def ler_arquivo(nome_arquivo):
    with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
        linhas = [linha.strip() for linha in arquivo.readlines() if linha.strip()]

    if not linhas:
        raise ValueError("Arquivo vazio")

    linha_fo = linhas[0]
    if not linha_fo.upper().startswith('MAX'):
        raise ValueError("Deve começar com 'Max'")

    fo_str = linha_fo[3:].strip()
    coef_fo = extrair_coeficientes(fo_str)
    
    restricoes = []
    vars_irrestritas = set()
    
    for linha in linhas[1:]:
        if re.match(r'^[xX]\d+\s*>=\s*0$', linha):
            continue
        
        if re.match(r'^[xX](\d+)\s*E\s*IR$', linha, re.IGNORECASE):
            var_num = int(re.match(r'^[xX](\d+)\s*E\s*IR$', linha, re.IGNORECASE).group(1))
            vars_irrestritas.add(var_num)
            continue

        match = re.match(r'(.+?)(<=|>=|=)(.+)', linha)
        if match:
            lhs, op, rhs = match.groups()
            coef_restr = extrair_coeficientes(lhs)
            restricoes.append((coef_restr, float(rhs.strip()), op))

    return coef_fo, restricoes, vars_irrestritas

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

def expandir_irrestritas(coef_fo, restricoes, vars_irrestritas):
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

def montar_tableau(coef_fo, restricoes, vars_irrestritas):
    coef_fo, restricoes = expandir_irrestritas(coef_fo, restricoes, vars_irrestritas)
    
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
    
    return np.array(A), np.array(b), var_names, c, basic_vars

def formatar(val):
    if abs(val) > 1000:
        return f"{val:.0f}"
    if abs(val - round(val)) < 1e-10:
        return int(round(val))
    return round(val, 2)

def imprimir(A, b, var_names, c, basic_vars, it=0):
    m, n = A.shape
    c_B = np.array([c[basic_vars[i]] for i in range(m)])
    z = -np.array(c) + c_B @ A
    z_b = c_B @ b
    
    headers = ["VB", "-Z"] + var_names + ["b"]
    dados = []
    
    for i in range(m):
        linha = [var_names[basic_vars[i]], 0]
        linha += [formatar(A[i,j]) for j in range(n)]
        linha += [formatar(b[i])]
        dados.append(linha)
    
    linha_z = ["-Z", 1] + [formatar(z[j]) for j in range(n)] + [formatar(z_b)]
    dados.append(linha_z)
    
    print("\n" + "="*80)
    print(f"ITERACAO {it}")
    print("="*80)
    print(tabulate(dados, headers=headers, tablefmt="grid"))
    
    return z, z_b

def simplex(A, b, var_names, c, basic_vars):
    it = 0
    
    while it < 100:
        z, z_b = imprimir(A, b, var_names, c, basic_vars, it)
        
        if all(z[j] >= -1e-10 for j in range(len(z))):
            if any(var_names[basic_vars[i]].startswith('a') for i in range(len(basic_vars))):
                print("\nINVIAVEL")
                return False
            print("\nOTIMO")
            return True
        
        col = np.argmin(z)
        
        if all(A[i, col] <= 1e-10 for i in range(len(b))):
            print("\nILIMITADO")
            return False
        
        razoes = []
        for i in range(len(b)):
            if A[i, col] > 1e-10:
                razoes.append((b[i] / A[i, col], i))
            else:
                razoes.append((float('inf'), i))
        
        _, lin = min(razoes)
        
        pivo = A[lin, col]
        A[lin] = A[lin] / pivo
        b[lin] = b[lin] / pivo
        
        for i in range(len(b)):
            if i != lin:
                fator = A[i, col]
                A[i] = A[i] - fator * A[lin]
                b[i] = b[i] - fator * b[lin]
        
        basic_vars[lin] = col
        it += 1
    
    return False

def main():
    arquivo = 'exemplo.txt'
    
    coef_fo, restricoes, vars_irrestritas = ler_arquivo(arquivo)
    A, b, var_names, c, basic_vars = montar_tableau(coef_fo, restricoes, vars_irrestritas)
    
    print("\nPROBLEMA:")
    print(f"FO: {coef_fo}")
    print(f"Restricoes: {len(restricoes)}")
    print(f"Variaveis irrestritas: {vars_irrestritas if vars_irrestritas else 'Nenhuma'}")
    
    sucesso = simplex(A, b, var_names, c, basic_vars)
    
    if sucesso:
        sbf = [0.0] * len(var_names)
        for i, idx in enumerate(basic_vars):
            sbf[idx] = b[i]
        
        print("\nSOLUCAO:")
        for i, var in enumerate(var_names):
            if not var.startswith('a') and sbf[i] != 0:
                print(f"{var} = {formatar(sbf[i])}")

if __name__ == "__main__":
    main()