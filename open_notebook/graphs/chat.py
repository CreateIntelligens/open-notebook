import asyncio
import sqlite3
from typing import Annotated, Optional

from ai_prompter import Prompter
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.config import LANGGRAPH_CHECKPOINT_FILE
from open_notebook.domain.notebook import Notebook
from open_notebook.utils import clean_thinking_content


class ThreadState(TypedDict):
    messages: Annotated[list, add_messages]
    notebook: Optional[Notebook]
    context: Optional[dict]
    context_config: Optional[dict]
    model_override: Optional[str]
    custom_system_prompt: Optional[str]
    include_citations: Optional[bool]


def call_model_with_messages(state: ThreadState, config: RunnableConfig) -> dict:
    # Use custom system prompt if provided, otherwise use default template
    custom_prompt = state.get("custom_system_prompt")
    include_citations = state.get("include_citations", True)

    if custom_prompt:
        # Build context string from state
        context_str = ""
        context_data = state.get("context", {})

        # Add sources to context
        if context_data and "sources" in context_data:
            for source in context_data["sources"]:
                source_id = source.get("id", "unknown")
                # Only show ID in context if citations are enabled
                if include_citations:
                    context_str += (
                        f"\n\n## Source: {source.get('title', 'Unknown')} [ID: {source_id}]\n"
                    )
                else:
                    context_str += (
                        f"\n\n## Source: {source.get('title', 'Unknown')}\n"
                    )

                # Add full text content if available (for "full content" mode)
                if "full_text" in source:
                    context_str += f"\n### Full Content\n{source.get('full_text', '')}\n"

                # Add insights if available (for "insights" mode or as additional context)
                if "insights" in source:
                    for insight in source["insights"]:
                        insight_id = insight.get("id", "unknown")
                        insight_type = insight.get("insight_type", "Insight")
                        # Only show ID in context if citations are enabled
                        if include_citations:
                            context_str += (
                                f"\n### {insight_type} [ID: {insight_id}]\n{insight.get('content', '')}\n"
                            )
                        else:
                            context_str += (
                                f"\n### {insight_type}\n{insight.get('content', '')}\n"
                            )

        # Add notes to context
        if context_data and "notes" in context_data:
            for note in context_data["notes"]:
                note_id = note.get("id", "unknown")
                # Only show ID in context if citations are enabled
                if include_citations:
                    context_str += (
                        f"\n\n## Note: {note.get('title', 'Unknown')} [ID: {note_id}]\n{note.get('content', '')}\n"
                    )
                else:
                    context_str += (
                        f"\n\n## Note: {note.get('title', 'Unknown')}\n{note.get('content', '')}\n"
                    )

        # Combine custom prompt with context
        if context_str:
            # Only add citing instructions if citations are enabled
            if include_citations:
                citing_instructions = """
# CITING INSTRUCTIONS
If your answer is based on any item in the context above, add references to the documents by including the document ID in brackets like this: [document_id].

Example: According to the regulations [source_insight:abc123], cosmetic labeling must include...

IMPORTANT:
- Use document IDs exactly as provided in the context
- IDs have prefixes like "source:", "source_insight:", "note:"
- Do not make up or modify document IDs
"""
            else:
                citing_instructions = ""

            system_prompt = f"""{custom_prompt}

IMPORTANT: You must follow the role and behavior described above in your current response, regardless of what role you may have taken in previous messages.

# Context Information
{context_str}
{citing_instructions}"""
        else:
            system_prompt = (
                f"{custom_prompt}\n\nIMPORTANT: You must follow the role and behavior described above in your current response, regardless of what role you may have taken in previous messages."
            )
    else:
        # Use default chat template
        if include_citations:
            # Standard mode: use Prompter with full context including IDs
            system_prompt = Prompter(prompt_template="chat/system").render(data=state)  # type: ignore[arg-type]
        else:
            # No-citation mode: build context without IDs and without citation instructions
            context_str = ""
            context_data = state.get("context", {})

            # Add sources to context (without IDs)
            if context_data and "sources" in context_data:
                for source in context_data["sources"]:
                    context_str += f"\n\n## Source: {source.get('title', 'Unknown')}\n"

                    # Add full text content if available
                    if "full_text" in source:
                        context_str += (
                            f"\n### Full Content\n{source.get('full_text', '')}\n"
                        )

                    # Add insights if available
                    if "insights" in source:
                        for insight in source["insights"]:
                            insight_type = insight.get("insight_type", "Insight")
                            context_str += (
                                f"\n### {insight_type}\n{insight.get('content', '')}\n"
                            )

            # Add notes to context (without IDs)
            if context_data and "notes" in context_data:
                for note in context_data["notes"]:
                    context_str += f"\n\n## Note: {note.get('title', 'Unknown')}\n{note.get('content', '')}\n"

            # Build system prompt without citation instructions
            if context_str:
                system_prompt = f"""You are a helpful AI assistant. Use the context information below to answer questions accurately.

# Context Information
{context_str}

Please provide your answers based on the context provided. Respond naturally without including document references or IDs."""
            else:
                system_prompt = "You are a helpful AI assistant."
    payload = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    model_id = config.get("configurable", {}).get("model_id") or state.get(
        "model_override"
    )

    # Handle async model provisioning from sync context
    def run_in_new_loop():
        """Run the async function in a new event loop"""
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(
                provision_langchain_model(
                    str(payload), model_id, "chat", max_tokens=8192
                )
            )
        finally:
            new_loop.close()
            asyncio.set_event_loop(None)

    try:
        # Try to get the current event loop
        asyncio.get_running_loop()
        # If we're in an event loop, run in a thread with a new loop
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_new_loop)
            model = future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        model = asyncio.run(
            provision_langchain_model(
                str(payload),
                model_id,
                "chat",
                max_tokens=8192,
            )
        )

    ai_message = model.invoke(payload)

    # Clean thinking content from AI response (e.g., <think>...</think> tags)
    content = (
        ai_message.content
        if isinstance(ai_message.content, str)
        else str(ai_message.content)
    )
    cleaned_content = clean_thinking_content(content)
    cleaned_message = ai_message.model_copy(update={"content": cleaned_content})

    return {"messages": cleaned_message}


conn = sqlite3.connect(
    LANGGRAPH_CHECKPOINT_FILE,
    check_same_thread=False,
)
memory = SqliteSaver(conn)

agent_state = StateGraph(ThreadState)
agent_state.add_node("agent", call_model_with_messages)
agent_state.add_edge(START, "agent")
agent_state.add_edge("agent", END)
graph = agent_state.compile(checkpointer=memory)
