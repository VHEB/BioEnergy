
<h1 align="center"> BioEnergy </h1>


<p align="center">
  <a href="#-guia">Guia</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#book-bibliotecas">Bibliotecas</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#-projeto">Projeto</a>&nbsp;&nbsp;&nbsp; |&nbsp;&nbsp;&nbsp;
  <a href="#email-contato">Contato</a>&nbsp;&nbsp;&nbsp;
</p>

## 🚀 **Guia**

Este guia descreve como clonar o repositório, configurar o ambiente e iniciar o projeto. Siga os passos abaixo para configurar o projeto localmente.

---

 1 - **Clone do Repositório**

Primeiro, clone o repositório para sua máquina local:

```bash
git clone https://github.com/VHEB/BioEnergy.git
```

Navegue até a pasta do projeto.

---

## 2 - **Crie um Ambiente Virtual**

Crie e ative um ambiente virtual para isolar as dependências do projeto:

### **Windows**

1. Crie o ambiente virtual:
   ```bash
   python -m venv .venv
   ```

2. Ative o ambiente virtual:
   ```bash
   .venv\Scripts\activate
   ```

### **macOS/Linux**

1. Crie o ambiente virtual:
   ```bash
   python3 -m venv .venv
   ```

2. Ative o ambiente virtual:
   ```bash
   source .venv/bin/activate
   ```

Quando o ambiente virtual estiver ativo, você verá algo semelhante a `(venv)` no início da linha de comando.

---

## 3 - **Instale as Dependências**

Com o ambiente virtual ativo, instale as dependências do projeto listadas no arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 4 - **Verifique o Setup**

Certifique-se de que todas as dependências foram instaladas corretamente executando o comando:

```bash
pip list
```

---

## 5 - **Inicie o Projeto**

Agora você está pronto para executar o projeto!

Rode o código abaixo no terminal e divirta-se.
```bash
streamlit run app.py
```

## :book: **Bibliotecas**

Esse projeto foi desenvolvido com as seguintes bibliotecas, linguagens e ferramentas:

- Python
   - Streamlit
   - Pandas

## 💻 **Projeto**

O projeto `BioEnergy` visa criar uma plataforma que oferece aos usuários dashboards interativos, podendo visualizar a produção de energia, a partir de `fontes renováveis` geradas no Brasil.

## :email: **Contato**

Se precisar de ajuda, sinta-se à vontade para perguntar!

Você também pode me encontrar no [LinkedIn](https://www.linkedin.com/in/vitor-heb/).

