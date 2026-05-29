# Validador de Atendimento WhatsApp

Aplicativo Streamlit para registrar testes de automações de atendimento, marcar conformidade e gerar relatório em CSV.

## Acesso

O app lê as credenciais pelos secrets do Streamlit:

```toml
APP_USERNAME = "Valenet"
APP_PASSWORD = "Valenet2026"
```

O arquivo local `.streamlit/secrets.toml` não deve ser enviado ao GitHub.

## Rodar localmente

```powershell
python -m streamlit run streamlit_app.py
```

## Publicar no Streamlit Community Cloud

1. Suba este projeto para o GitHub.
2. Acesse `https://share.streamlit.io`.
3. Escolha o repositório e o arquivo `streamlit_app.py`.
4. Em `Advanced settings`, adicione os secrets acima.
5. Clique em `Deploy`.
