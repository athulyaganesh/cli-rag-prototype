"""Streamlit web app: chat support and email drafting on the same RAG backend.

Run locally: streamlit run src/app.py
Documents are indexed separately with src/ingest.py.
"""

import hmac
import logging
import os

import streamlit as st
from dotenv import load_dotenv

from copilot import EMAIL_GREETING, EMAIL_SIGN_OFF, format_sources
from rag import AnswerResult, Mode, answer

logger = logging.getLogger(__name__)


def is_authorized() -> bool:
    """True if APP_PASSWORD isn't set, or the visitor has entered it."""
    expected_password = os.getenv("APP_PASSWORD")
    if not expected_password or st.session_state.get("is_authorized"):
        return True
    entered_password = st.text_input("Password", type="password")
    if entered_password and hmac.compare_digest(
        entered_password.encode(), expected_password.encode()
    ):
        st.session_state.is_authorized = True
        st.rerun()
    elif entered_password:
        st.error("Wrong password.")
    return False


def ask(question: str, mode: Mode) -> AnswerResult | None:
    """Call answer(), showing any error in the page instead of crashing it."""
    try:
        with st.spinner("Searching the documentation..."):
            return answer(question, mode=mode)
    except Exception as error:
        logger.exception("answer() failed")
        st.error(f"Something went wrong: {type(error).__name__}: {error}")
        return None


def render_chat_result(result: AnswerResult) -> None:
    if result.escalate:
        st.warning(f"{result.answer}\n\nNeeds human review: {result.reason}")
    else:
        st.markdown(result.answer)
        st.markdown(f"**Sources**\n{format_sources(result.citations)}")


def render_chat_tab() -> None:
    history: list[tuple[str, AnswerResult]] = st.session_state.setdefault("chat_history", [])
    for question, result in history:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            render_chat_result(result)

    question = st.chat_input("Ask a question about the documentation")
    if question:
        result = ask(question, "chat")
        if result:
            history.append((question, result))
            st.rerun()


def render_email_tab() -> None:
    email_text = st.text_area("Customer email", height=200)
    if st.button("Draft reply", disabled=not email_text.strip()):
        st.session_state.email_result = ask(email_text.strip(), "email")

    result: AnswerResult | None = st.session_state.get("email_result")
    if result is None:
        return
    if result.escalate:
        st.warning(f"Needs human review: {result.reason}")
        return

    draft = st.text_area(
        "Suggested reply (edit before sending)",
        value=f"{EMAIL_GREETING}\n\n{result.answer}\n\n{EMAIL_SIGN_OFF}",
        height=300,
    )
    st.caption("Copy the final reply with the button in the box below.")
    st.code(draft, language=None)
    st.markdown(f"**Sources (check before sending)**\n{format_sources(result.citations)}")


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    st.set_page_config(page_title="Support Copilot")
    st.title("Support Copilot")
    if not is_authorized():
        return

    chat_tab, email_tab = st.tabs(["Chat Support", "Email Support"])
    with chat_tab:
        render_chat_tab()
    with email_tab:
        render_email_tab()


if __name__ == "__main__":
    main()
