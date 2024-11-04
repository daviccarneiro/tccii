import streamlit as st
from notion_client import Client
import datetime
import openai

# Configuração do cliente Notion (substitua com sua chave de integração)
notion = Client(auth=st.secrets["NOTION_TOKEN"])

# ID do banco de dados do Notion (substitua com o ID do seu banco de dados)
DATABASE_ID = "1333918868ec8043896ce777ce180e42"

# Token da API da OpenAI
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Função para enviar dados ao Notion
def enviar_para_notion(dados, especialidade):
    response = notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "Nome": {"title": [{"text": {"content": dados["nome"]}}]},
            "Sobrenome": {"rich_text": [{"text": {"content": dados["sobrenome"]}}]},
            "Endereço": {"rich_text": [{"text": {"content": dados["endereco"]}}]},
            "Data de Nascimento": {"date": {"start": dados["data_nascimento"].isoformat()}},
            "CPF": {"rich_text": [{"text": {"content": dados["cpf"]}}]},
            "Telefone": {"phone_number": dados["telefone"]},
            "Email": {"email": {"content": dados["email"]}},
            "Queixa Principal": {"rich_text": [{"text": {"content": dados["queixa_principal"]}}]},
            "Alergias Medicamentosas": {"rich_text": [{"text": {"content": dados["alergias"]}}]},
            "Uso de Medicamentos": {"rich_text": [{"text": {"content": dados["medicamentos"]}}]},
            "Bebe": {"checkbox": dados["bebe"]},
            "Fuma": {"checkbox": dados["fuma"]},
            "Escovações por Dia": {"number": dados["escovacoes_por_dia"]},
            "Status": {"status": {"name": "Pendente"}},
            "Especialidade Recomendada": {"multi_select": [{"name": especialidade}]}
        }
    )
    return response

# Função para obter a especialidade recomendada usando a API da OpenAI com o modelo de chat
def obter_especialidade_recomendada(queixa):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente que recomenda especialidades odontológicas."},
                {"role": "user", "content": f"A queixa do paciente é: '{queixa}'. Responda com apenas o nome da especialidade odontológica recomendada para este caso, sem explicações adicionais. Você poderá apenas escolher entre as opções: Ortodontia, Endodontia, Periodontia, Cirurgia, Dentística, Prótese, Odontopediatria, Estomatologia, Radiologia, Harmonização Facial e Implantodontia. Não coloque o ponto final na mensagem."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        especialidade = response['choices'][0]['message']['content'].strip()
        return especialidade
    except Exception as e:
        st.error(f"Erro ao consultar a API da OpenAI: {e}")
        return "Erro"

# Função para verificar o status da consulta no Notion pelo CPF
def verificar_status_cpf(cpf):
    query = notion.databases.query(
        **{
            "database_id": DATABASE_ID,
            "filter": {
                "property": "CPF",
                "rich_text": {
                    "equals": cpf
                }
            }
        }
    )
    
    if query["results"]:
        status = query["results"][0]["properties"]["Status"]["status"]["name"]
        return status
    else:
        return None

# Função para a tela inicial
def tela_inicial():
    st.title("Sistema de Agendamento Odontológico")
    st.write("Selecione uma opção:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Nova Consulta"):
            st.session_state.pagina = "nova_consulta"
            st.query_params(page="nova_consulta")
    with col2:
        if st.button("Verificar Status de Consulta"):
            st.session_state.pagina = "verificar_status"
            st.query_params(page="verificar_status")

# Tela de nova consulta
def tela_nova_consulta():
    st.header("Agendamento de Nova Consulta")
    if st.button("⬅ Voltar"):
        st.session_state.pagina = "inicial"
        st.query_params(page="inicial")

    with st.form("consulta_form"):
        nome = st.text_input("Nome")
        sobrenome = st.text_input("Sobrenome")
        endereco = st.text_input("Endereço")
        data_nascimento = st.date_input("Data de Nascimento", datetime.date(2000, 1, 1))
        cpf = st.text_input("CPF")
        telefone = st.text_input("Telefone")
        email = st.text_input("Email")
        queixa_principal = st.text_area("Queixa Principal")
        alergias = st.text_area("Alergias Medicamentosas")
        medicamentos = st.text_area("Uso de Medicamentos")
        bebe = st.checkbox("Bebe")
        fuma = st.checkbox("Fuma")
        escovacoes_por_dia = st.number_input("Quantidade de Escovações por Dia", min_value=0, max_value=10, step=1)

        submit_button = st.form_submit_button("Agendar Consulta")
        
        if submit_button:
            dados = {
                "nome": nome,
                "sobrenome": sobrenome,
                "endereco": endereco,
                "data_nascimento": data_nascimento,
                "cpf": cpf,
                "telefone": telefone,
                "email": email,
                "queixa_principal": queixa_principal,
                "alergias": alergias,
                "medicamentos": medicamentos,
                "bebe": bebe,
                "fuma": fuma,
                "escovacoes_por_dia": escovacoes_por_dia,
            }

            especialidade = obter_especialidade_recomendada(queixa_principal)
            enviar_para_notion(dados, especialidade)
            
            st.session_state.especialidade = especialidade
            st.session_state.pagina = "confirmacao"
            st.query_params(page="confirmacao")

# Tela de confirmação após o agendamento
def tela_confirmacao():
    st.header("Consulta Agendada com Sucesso!")
    st.write(f"Especialidade recomendada: **{st.session_state.especialidade}**")
    st.info("Seus dados foram enviados com sucesso! Em breve, entraremos em contato para confirmar a data da sua consulta.")
    if st.button("Voltar ao início"):
        st.session_state.pagina = "inicial"
        st.query_params(page="inicial")

# Tela de verificação de status de consulta
def tela_verificar_status():
    st.header("Verificar Status da Consulta")
    if st.button("⬅ Voltar"):
        st.session_state.pagina = "inicial"
        st.query_params(page="inicial")

    cpf = st.text_input("Informe o CPF para verificar o status")
    verificar_button = st.button("Verificar")
    
    if verificar_button and cpf:
        status = verificar_status_cpf(cpf)
        if status:
            st.write(f"O status da consulta é: **{status}**")
        else:
            st.error("Consulta não encontrada para o CPF informado.")

# Controle de navegação entre telas
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicial"

# Renderiza a tela com base no estado atual
if st.session_state.pagina == "inicial":
    tela_inicial()
elif st.session_state.pagina == "nova_consulta":
    tela_nova_consulta()
elif st.session_state.pagina == "confirmacao":
    tela_confirmacao()
elif st.session_state.pagina == "verificar_status":
    tela_verificar_status()
