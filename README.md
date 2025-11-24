# Simplex-Solver

Implementação do **Método Simplex** em Python para resolver problemas de Programação Linear (PL). O programa lê problemas de um arquivo de texto, resolve utilizando o algoritmo Simplex com o Método Big-M, e gera relatórios detalhados das iterações.

---

## 📋 Características

- ✅ Suporte para problemas de **Maximização** e **Minimização**
- ✅ Restrições dos tipos: `<=`, `>=` e `=`
- ✅ Variáveis com domínios: `>= 0`, `<= 0` e **livres (irrestritas)**
- ✅ Método Big-M para variáveis artificiais
- ✅ Detecção de soluções: **Ótima**, **Inviável** e **Ilimitada**
- ✅ Exportação automática de resultados em arquivos `.txt`
- ✅ Tabelas formatadas para fácil visualização

---

## 🚀 Como Usar

### 1. Instalação de Dependências

```bash
pip install numpy tabulate
```

### 2. Formato do Arquivo de Entrada

Crie um arquivo `exemplo.txt` seguindo o formato abaixo:

```
MAX 3 x1 + 2 x2 + 10 x3 + 0 x4 + 2 x5

3 x1 + 1 x2 + 7 x3 + 10 x4 + 0 x5 <= 6
1 x1 + 0 x2 + 7 x3 + 0 x4 + 9 x5 >= 46
8 x1 + 0 x2 + 1 x3 + 1 x4 + 1 x5 >= 25
3 x1 + 3 x2 + 1 x3 + 3 x4 + 9 x5 <= 29
4 x1 + 4 x2 + 8 x3 + 7 x4 + 0 x5 = 19

x1 >= 0
x2 >= 0
x3 >= 0
x4 <= 0
x5 livre
```

#### 📝 Estrutura do Arquivo:

1. **Linha 1**: Função Objetivo
   - Inicia com `MAX` ou `MIN`
   - Formato: `coeficiente espaço variável espaço sinal`
   - Exemplo: `MAX 3 x1 + 2 x2 - 5 x3`

2. **Linha 2**: **Linha em branco** (obrigatória)

3. **Linhas 3+**: Restrições
   - Formato: `coeficientes operador RHS`
   - Operadores: `<=`, `>=` ou `=`
   - Exemplo: `2 x1 + 3 x2 <= 10`

4. **Linha em branco** após restrições

5. **Linhas finais**: Domínio das variáveis
   - `x1 >= 0` (não-negativa, padrão)
   - `x4 <= 0` (não-positiva)
   - `x5 livre` (irrestrita, pode ser qualquer valor)

### 3. Executar o Programa

```bash
python main.py
```

---

## 📊 Saída do Programa

### Console
O programa exibe:
- Informações do problema
- Tableau de cada iteração
- Resultado final (ÓTIMO/INVIÁVEL/ILIMITADO)
- Valores das variáveis na solução ótima

### Arquivo de Resultado
Cria automaticamente arquivos `resultado1.txt`, `resultado2.txt`, etc., contendo:
- Dados do problema original
- Todas as iterações do Simplex
- Solução final

**Exemplo de saída:**
```
PROBLEMA:
Sense: MAX
FO: [3.0, 2.0, 10.0, 0.0, 2.0]
Restricoes: 5
Variaveis irrestritas: {5}
Variaveis negativas: {4}

================================================================================
ITERACAO 0
================================================================================
╒══════╤══════╤══════╤══════╤═══╤══════╤══════╤══════╤═══════╕
│ VB   │   -Z │   x1 │   x2 │...│   a5 │    b │
╞══════╪══════╪══════╪══════╪═══╪══════╪══════╪══════╪═══════╡
│ f1   │    0 │    3 │    1 │...│    0 │    6 │
│ a2   │    0 │    1 │    0 │...│    0 │   46 │
...
│ -Z   │    1 │   -3 │   -2 │...│    0 │    0 │
╘══════╧══════╧══════╧══════╧═══╧══════╧══════╧══════╧═══════╛

OTIMO

SOLUCAO:
x1 = 5.0
x2 = 3.0
```

---

## 🧮 Como Funciona

### 1. **Leitura e Parsing**
```python
ler_arquivo('exemplo.txt')
```
- Extrai função objetivo, restrições e domínios
- Identifica variáveis especiais (livres/negativas)

### 2. **Expansão de Variáveis**
```python
expandir_irrestritas(...)
```
- **Variáveis negativas** (`x <= 0`): Substitui por `-y` onde `y >= 0`
- **Variáveis livres** (`x livre`): Substitui por `x⁺ - x⁻` onde ambas `>= 0`

### 3. **Montagem do Tableau**
```python
montar_tableau(...)
```
Adiciona variáveis auxiliares:
- **Folga (f)**: Para restrições `<=`
- **Excesso (e)**: Para restrições `>=`
- **Artificial (a)**: Para restrições `>=` e `=`

Exemplo:
```
x1 + x2 <= 5    →    x1 + x2 + f1 = 5
x1 + x2 >= 3    →    x1 + x2 - e2 + a2 = 3
x1 + x2 = 4     →    x1 + x2 + a3 = 4
```

### 4. **Método Simplex**
```python
simplex(...)
```
**Iteração:**
1. **Teste de Otimalidade**: Se todos custos reduzidos `>= 0` → FIM
2. **Escolha da variável que entra**: Menor custo reduzido (mais negativo)
3. **Teste de Ilimitação**: Se nenhum coeficiente positivo → ILIMITADO
4. **Escolha da variável que sai**: Regra do menor quociente `b[i] / a[i,col]`
5. **Pivoteamento**: Atualiza tableau

**Método Big-M:**
- Variáveis artificiais têm custo `-M` (M = 1.000.000)
- Força artificiais a sair da base
- Se artificial permanece → Problema INVIÁVEL

---

## 📁 Estrutura do Projeto

```
Simplex-Solver/
│
├── main.py                  # Código principal
├── exemplo.txt              # Arquivo de entrada de exemplo
├── resultado1.txt           # Saída gerada (auto-incremental)
├── resultado2.txt
└── README.md               # Este arquivo
```

---

## 🔧 Funções Principais

| Função | Descrição |
|--------|-----------|
| `ler_arquivo()` | Lê e valida arquivo de entrada |
| `extrair_coeficientes()` | Parseia expressões como "3x1 + 2x2" |
| `expandir_irrestritas()` | Trata variáveis livres e negativas |
| `montar_tableau()` | Cria tableau inicial com variáveis auxiliares |
| `simplex()` | Executa algoritmo Simplex |
| `imprimir()` | Formata e exibe tableau |
| `obter_proximo_arquivo_resultado()` | Gerencia numeração de arquivos de saída |

---

## 📖 Nomenclatura

| Símbolo | Significado | Uso |
|---------|-------------|-----|
| **x** | Variável de decisão | Variáveis do problema original |
| **f** | Folga (*slack*) | Restrições `<=` |
| **e** | Excesso (*surplus*) | Restrições `>=` |
| **a** | Artificial | Restrições `>=` e `=` |
| **VB** | Variáveis Básicas | Variáveis na base atual |
| **-Z** | Negativo da FO | Linha de custos reduzidos |

---

## ⚠️ Limitações

- Máximo de 100 iterações (evita loops infinitos)
- `BIG_M = 1.000.000` (pode precisar ajuste para problemas específicos)
- Não detecta múltiplas soluções ótimas
- Não implementa método Dual Simplex

---

## 🎓 Conceitos Teóricos

### Programação Linear
Otimiza função objetivo linear sujeita a restrições lineares:
```
MAX/MIN  c₁x₁ + c₂x₂ + ... + cₙxₙ
s.a.     a₁₁x₁ + a₁₂x₂ + ... + a₁ₙxₙ  ≤/≥/=  b₁
         ...
         xᵢ ≥ 0, xⱼ ≤ 0, xₖ livre
```

### Método Simplex
Algoritmo que:
1. Parte de vértice viável
2. Move para vértices adjacentes melhorando FO
3. Para quando nenhum vizinho melhora (ótimo)

### Método Big-M
Técnica para lidar com artificiais:
- Adiciona penalidade `-M` na FO
- Força artificiais a sair da base
- Se artificial fica → Inviável

---

## 📚 Referências

- Bazaraa, M. S., Jarvis, J. J., & Sherali, H. D. (2010). *Linear Programming and Network Flows*. Wiley.
- Hillier, F. S., & Lieberman, G. J. (2015). *Introduction to Operations Research*. McGraw-Hill.

---

## 👨‍💻 Autor

Desenvolvido para disciplina de Otimização - BCC

---

## 📄 Licença

Este projeto é de uso acadêmico.