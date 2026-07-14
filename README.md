# Validador de Atendimento WhatsApp

Aplicativo Streamlit para registrar testes de automações de atendimento, marcar conformidade e gerar relatório em CSV.

## Acesso

O app lê o usuário e a senha inicial pelos secrets do Streamlit:

```toml
APP_USERNAME = "Valenet"
APP_PASSWORD = "Valenet2026"
```

A senha inicial é provisória. No primeiro acesso, o app exige a troca e passa a validar a nova senha por hash salvo em `.streamlit_runtime/auth.json`.

Se o app estiver usando banco externo, como Neon, e ninguém conseguir acessar, use os
secrets de reset emergencial:

```toml
APP_RESET_USERNAME = "Eduardo"
APP_RESET_PASSWORD = "senha_provisoria_nova"
APP_RESET_VERSION = "2026-07-14-1"
```

Ao iniciar, o app redefine esse usuário no banco, marca a senha como provisória e
exige a troca no próximo login. Para repetir o reset no futuro, altere
`APP_RESET_VERSION`.

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
