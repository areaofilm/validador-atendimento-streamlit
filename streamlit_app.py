from __future__ import annotations

from datetime import date
from io import StringIO
from pathlib import Path
import csv
import hashlib
import hmac
import json
import os
import uuid

import streamlit as st


AUTH_FILE = Path(".streamlit_runtime/auth.json")
PBKDF2_ITERATIONS = 390_000
MAX_IMAGE_SIZE_MB = 5


st.set_page_config(
    page_title="Validador WhatsApp",
    page_icon="OK",
    layout="wide",
)


def get_credentials() -> tuple[str, str]:
    username = os.getenv("APP_USERNAME") or st.secrets.get("APP_USERNAME", "")
    password = os.getenv("APP_PASSWORD") or st.secrets.get("APP_PASSWORD", "")
    return username, password


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or uuid.uuid4().hex
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, expected_digest = password_hash.split("$", 1)
    except ValueError:
        return False

    candidate = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, expected_digest)


def load_auth_record() -> dict[str, str] | None:
    if not AUTH_FILE.exists():
        return None

    try:
        return json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_new_password(password: str) -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(
        json.dumps({"password_hash": hash_password(password)}, indent=2),
        encoding="utf-8",
    )


def validate_login(username: str, password: str) -> tuple[bool, bool]:
    expected_username, initial_password = get_credentials()
    if username != expected_username:
        return False, False

    auth_record = load_auth_record()
    if auth_record and verify_password(password, auth_record.get("password_hash", "")):
        return True, False

    if not auth_record and password == initial_password:
        return True, True

    return False, False


def init_state() -> None:
    defaults = {
        "authenticated": False,
        "pending_password_change": False,
        "tests": [],
        "audit_name": "",
        "channel": "",
        "auditor": "",
        "audit_date": date.today(),
        "editing_id": None,
        "upload_version": 0,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def login_screen() -> None:
    expected_username, expected_password = get_credentials()

    st.markdown(
        """
        <style>
          .login-card {
            max-width: 460px;
            margin: 8vh auto 0;
            padding: 2rem;
            border: 1px solid #d8e2dc;
            border-radius: 8px;
            background: #ffffff;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.title("Validador de automações WhatsApp")
        st.caption("Acesso restrito para validação de fluxos de atendimento.")

        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)

        if submitted:
            valid_login, must_change_password = validate_login(username, password)
            if valid_login and must_change_password:
                st.session_state.pending_password_change = True
                st.session_state.authenticated = False
                st.rerun()
            elif valid_login:
                st.session_state.pending_password_change = False
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")

        if not expected_username or not expected_password:
            st.warning("Configure APP_USERNAME e APP_PASSWORD nos secrets do Streamlit.")


def password_change_screen() -> None:
    _, initial_password = get_credentials()

    with st.container(border=True):
        st.title("Trocar senha")
        st.caption("A senha inicial é provisória. Cadastre uma nova senha para liberar o app.")

        with st.form("change_password_form"):
            new_password = st.text_input("Nova senha", type="password")
            confirm_password = st.text_input("Confirmar nova senha", type="password")
            submitted = st.form_submit_button("Salvar nova senha", use_container_width=True)

        if not submitted:
            return

        if len(new_password) < 8:
            st.error("A nova senha precisa ter pelo menos 8 caracteres.")
            return

        if new_password == initial_password:
            st.error("A nova senha deve ser diferente da senha provisória.")
            return

        if new_password != confirm_password:
            st.error("A confirmação não confere com a nova senha.")
            return

        save_new_password(new_password)
        st.session_state.pending_password_change = False
        st.session_state.authenticated = True
        st.success("Senha alterada com sucesso.")
        st.rerun()


def status_label(status: str) -> str:
    labels = {
        "conforme": "Conforme",
        "nao-conforme": "Não conforme",
        "pendente": "Pendente",
    }
    return labels.get(status, "Pendente")


def calculate_summary() -> dict[str, int]:
    tests = st.session_state.tests
    conform = sum(1 for item in tests if item["status"] == "conforme")
    non_conform = sum(1 for item in tests if item["status"] == "nao-conforme")
    evaluated = conform + non_conform
    rate = round((conform / evaluated) * 100) if evaluated else 0

    return {
        "total": len(tests),
        "conform": conform,
        "non_conform": non_conform,
        "rate": rate,
    }


def make_csv() -> str:
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    summary = calculate_summary()

    writer.writerow(["Bateria", st.session_state.audit_name])
    writer.writerow(["Canal", st.session_state.channel])
    writer.writerow(["Responsável", st.session_state.auditor])
    writer.writerow(["Data", st.session_state.audit_date.strftime("%d/%m/%Y")])
    writer.writerow(["Total", summary["total"]])
    writer.writerow(["Conformes", summary["conform"]])
    writer.writerow(["Não conformes", summary["non_conform"]])
    writer.writerow(["Percentual de conformidade", f'{summary["rate"]}%'])
    writer.writerow([])
    writer.writerow(["Teste", "Status", "Cenário", "Esperado", "Observações", "Anexos"])

    for test in st.session_state.tests:
        attachment_names = ", ".join(
            attachment["name"] for attachment in test.get("attachments", [])
        )
        writer.writerow(
            [
                test["title"],
                status_label(test["status"]),
                test["scenario"],
                test["expected"],
                test["notes"],
                attachment_names,
            ]
        )

    return output.getvalue()


def reset_form() -> None:
    st.session_state.editing_id = None
    for key in ("title_input", "scenario_input", "expected_input", "notes_input"):
        st.session_state[key] = ""
    st.session_state.status_input = "conforme"
    st.session_state.upload_version += 1


def uploaded_images() -> list[dict[str, object]]:
    key = f"attachments_input_{st.session_state.upload_version}"
    files = st.session_state.get(key) or []
    attachments = []

    for file in files:
        data = file.getvalue()
        size_mb = len(data) / (1024 * 1024)
        if size_mb > MAX_IMAGE_SIZE_MB:
            st.warning(
                f"{file.name} foi ignorado. Limite: {MAX_IMAGE_SIZE_MB} MB por imagem."
            )
            continue

        attachments.append(
            {
                "name": file.name,
                "type": file.type,
                "data": data,
            }
        )

    return attachments


def save_test() -> None:
    title = st.session_state.title_input.strip()
    if not title:
        st.warning("Informe o que será testado antes de salvar.")
        return

    payload = {
        "id": st.session_state.editing_id or str(uuid.uuid4()),
        "title": title,
        "scenario": st.session_state.scenario_input.strip(),
        "expected": st.session_state.expected_input.strip(),
        "notes": st.session_state.notes_input.strip(),
        "status": st.session_state.status_input,
        "attachments": uploaded_images(),
    }

    if st.session_state.editing_id:
        current = next(
            (item for item in st.session_state.tests if item["id"] == st.session_state.editing_id),
            None,
        )
        existing_attachments = current.get("attachments", []) if current else []
        payload["attachments"] = existing_attachments + payload["attachments"]
        st.session_state.tests = [
            payload if item["id"] == st.session_state.editing_id else item
            for item in st.session_state.tests
        ]
    else:
        st.session_state.tests.insert(0, payload)

    reset_form()
    st.success("Teste salvo.")


def edit_test(test_id: str) -> None:
    test = next((item for item in st.session_state.tests if item["id"] == test_id), None)
    if not test:
        return

    st.session_state.editing_id = test_id
    st.session_state.title_input = test["title"]
    st.session_state.scenario_input = test["scenario"]
    st.session_state.expected_input = test["expected"]
    st.session_state.notes_input = test["notes"]
    st.session_state.status_input = test["status"]
    st.session_state.upload_version += 1


def delete_test(test_id: str) -> None:
    st.session_state.tests = [
        item for item in st.session_state.tests if item["id"] != test_id
    ]
    if st.session_state.editing_id == test_id:
        reset_form()


def render_header() -> None:
    left, right = st.columns([0.75, 0.25], vertical_alignment="center")
    with left:
        st.title("Validador de automações WhatsApp")
        st.caption("Registro de testes, conformidade e evidências do atendimento.")
    with right:
        if st.button("Sair", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.pending_password_change = False
            st.rerun()


def render_summary() -> None:
    summary = calculate_summary()
    cols = st.columns(4)
    cols[0].metric("Total de testes", summary["total"])
    cols[1].metric("Conformes", summary["conform"])
    cols[2].metric("Não conformes", summary["non_conform"])
    cols[3].metric("Conformidade", f'{summary["rate"]}%')


def render_audit_data() -> None:
    st.subheader("Dados da bateria")
    cols = st.columns(4)
    with cols[0]:
        st.text_input("Nome da bateria", key="audit_name")
    with cols[1]:
        st.text_input("Canal / número testado", key="channel")
    with cols[2]:
        st.text_input("Responsável", key="auditor")
    with cols[3]:
        st.date_input("Data", key="audit_date", format="DD/MM/YYYY")


def render_test_form() -> None:
    st.subheader("Novo teste")
    st.text_input(
        "O que vou testar",
        placeholder="Ex.: Segunda via de boleto",
        key="title_input",
    )

    cols = st.columns(2)
    with cols[0]:
        st.text_area(
            "Mensagem enviada / cenário",
            placeholder="Ex.: Cliente pergunta: Quero minha segunda via",
            key="scenario_input",
            height=120,
        )
        st.radio(
            "Resultado",
            options=["conforme", "nao-conforme", "pendente"],
            format_func=status_label,
            horizontal=True,
            key="status_input",
        )
    with cols[1]:
        st.text_area(
            "Resposta esperada da automação",
            placeholder="Ex.: Bot identifica o cliente e oferece link da segunda via",
            key="expected_input",
            height=120,
        )
        st.text_area(
            "Observações",
            placeholder="Evidências, horários, prints, falhas ou pontos de melhoria",
            key="notes_input",
            height=120,
        )

    upload_key = f"attachments_input_{st.session_state.upload_version}"
    files = st.file_uploader(
        "Evidências em imagem",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=upload_key,
        help="Aceita PNG, JPG e JPEG. Limite recomendado: 5 MB por imagem.",
    )

    if files:
        st.caption("Pré-visualização dos anexos")
        preview_cols = st.columns(min(3, len(files)))
        for index, file in enumerate(files):
            with preview_cols[index % len(preview_cols)]:
                st.image(file, caption=file.name, use_container_width=True)

    if st.session_state.editing_id:
        current = next(
            (item for item in st.session_state.tests if item["id"] == st.session_state.editing_id),
            None,
        )
        existing_attachments = current.get("attachments", []) if current else []
        if existing_attachments:
            st.caption("Anexos já salvos neste teste")
            preview_cols = st.columns(min(3, len(existing_attachments)))
            for index, attachment in enumerate(existing_attachments):
                with preview_cols[index % len(preview_cols)]:
                    st.image(
                        attachment["data"],
                        caption=attachment["name"],
                        use_container_width=True,
                    )

    label = "Salvar alteração" if st.session_state.editing_id else "Adicionar teste"
    cols = st.columns([0.25, 0.25, 0.5])
    with cols[0]:
        st.button(label, type="primary", use_container_width=True, on_click=save_test)
    with cols[1]:
        st.button("Cancelar edição", use_container_width=True, on_click=reset_form)


def render_report() -> None:
    st.subheader("Relatório final")

    summary = calculate_summary()
    st.write(
        f"**Bateria:** {st.session_state.audit_name or 'Não informado'}  \n"
        f"**Canal:** {st.session_state.channel or 'Não informado'}  \n"
        f"**Responsável:** {st.session_state.auditor or 'Não informado'}  \n"
        f"**Data:** {st.session_state.audit_date.strftime('%d/%m/%Y')}  \n"
        f"**Percentual de conformidade:** {summary['rate']}%"
    )

    csv_data = make_csv()
    st.download_button(
        "Baixar relatório CSV",
        data=csv_data.encode("utf-8-sig"),
        file_name=f"relatorio-testes-whatsapp-{st.session_state.audit_date}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if not st.session_state.tests:
        st.info("Nenhum teste cadastrado ainda.")
        return

    for index, test in enumerate(st.session_state.tests, start=1):
        with st.container(border=True):
            cols = st.columns([0.65, 0.35], vertical_alignment="center")
            with cols[0]:
                st.markdown(f"**Teste {index}: {test['title']}**")
            with cols[1]:
                st.markdown(f"**Resultado:** {status_label(test['status'])}")

            st.write(f"**Cenário:** {test['scenario'] or 'Não informado.'}")
            st.write(f"**Esperado:** {test['expected'] or 'Não informado.'}")
            st.write(f"**Observações:** {test['notes'] or 'Não informado.'}")

            attachments = test.get("attachments", [])
            if attachments:
                st.write("**Evidências:**")
                image_cols = st.columns(min(3, len(attachments)))
                for image_index, attachment in enumerate(attachments):
                    with image_cols[image_index % len(image_cols)]:
                        st.image(
                            attachment["data"],
                            caption=attachment["name"],
                            use_container_width=True,
                        )

            action_cols = st.columns([0.18, 0.18, 0.64])
            with action_cols[0]:
                st.button(
                    "Editar",
                    key=f"edit_{test['id']}",
                    use_container_width=True,
                    on_click=edit_test,
                    args=(test["id"],),
                )
            with action_cols[1]:
                st.button(
                    "Excluir",
                    key=f"delete_{test['id']}",
                    use_container_width=True,
                    on_click=delete_test,
                    args=(test["id"],),
                )


def main() -> None:
    init_state()

    if st.session_state.pending_password_change:
        password_change_screen()
        return

    if not st.session_state.authenticated:
        login_screen()
        return

    render_header()
    render_summary()
    st.divider()

    render_audit_data()
    st.divider()

    left, right = st.columns([0.52, 0.48], gap="large")
    with left:
        render_test_form()
    with right:
        render_report()


if __name__ == "__main__":
    main()
