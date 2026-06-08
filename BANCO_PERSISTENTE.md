# Banco persistente no Streamlit Cloud

O Streamlit Cloud pode reiniciar o app diariamente ou quando ele fica inativo.
Arquivos locais criados durante a execução, incluindo SQLite (`.db`), podem ser
perdidos nesses reinicios.

Para manter usuarios, senhas e relatorios apos reboot, configure um banco
PostgreSQL externo e adicione a URL do banco nos secrets do app:

```toml
DATABASE_URL = "postgresql://USUARIO:SENHA@HOST:PORTA/BANCO"
```

Onde configurar:

1. Abra o app no Streamlit Cloud.
2. Entre em **Settings**.
3. Abra **Secrets**.
4. Cole o `DATABASE_URL`.
5. Salve e reinicie o app.

Depois disso, no app, a area **Banco local** deve mostrar:

```text
Tipo: PostgreSQL externo
```

Se aparecer **SQLite local temporario**, os dados ainda podem sumir em reboot.

Esta mesma regra vale para os outros apps: se eles salvam dados em SQLite local
no Streamlit Cloud, precisam receber um PostgreSQL externo ou outro banco remoto.
