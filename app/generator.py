import re
import logging
from langchain_cohere import CohereEmbeddings, ChatCohere
from .config import settings
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_pinecone import PineconeVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

embedding = CohereEmbeddings(
    model="embed-v4.0",
    cohere_api_key=settings.COHERE_API_KEY,
    user_agent="LangChain",
)

chat = ChatCohere(verbose=True, cohere_api_key=settings.COHERE_API_KEY)

chat_history = []

MAX_HISTORY_LENGTH = 20


def add_message_to_history(message):
    """Add a message to the global chat history and trim if needed."""
    global chat_history
    chat_history.append(message)
    if len(chat_history) > MAX_HISTORY_LENGTH:
        chat_history = chat_history[-MAX_HISTORY_LENGTH:]


def extract_python_code(text: str) -> str:
    """Extract Python code from text that might contain markdown code blocks."""
    code_pattern = re.compile(r"```(?:python)?\s*([\s\S]*?)\s*```")
    matches = code_pattern.findall(text)
    return matches[0] if matches else text


def generate_manim_code(prompt: str) -> str:
    """Generate Manim code using Cohere model with improved retrieval context."""
    add_message_to_history(HumanMessage(content=prompt))

    query_enhancement_prompt = """
    I need to search for relevant Manim documentation to help with a technical visualization request.
    
    Original request: {input}
    
    Convert this into a search query that would effectively retrieve Manim documentation by:
    1. Identifying the core mathematical or visual concept (e.g., "vector field", "complex numbers", "graph theory")
    2. Including specific Manim classes or methods if mentioned (e.g., "ValueTracker", "MathTex", "ThreeDScene")
    3. Adding technical terms related to animation or visualization (e.g., "transformation", "coordinate system", "camera movement")
    4. Using Manim-specific terminology where applicable
    
    Format the query as a comma-separated list of relevant terms. If the original request mentions a mathematical theorem, include both the theorem name and the mathematical domain.
    
    Enhanced search query:"""

    try:
        enhanced_query_response = chat.invoke(
            input=query_enhancement_prompt.format(input=prompt)
        )
        enhanced_query = enhanced_query_response.content
        logger.info(f"Enhanced search query: {enhanced_query}")

        doc_search = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=embedding,
            pinecone_api_key=settings.PINECONE_API_KEY,
        )

        retriever = doc_search.as_retriever(search_kwargs={"k": 5})

        docs_original = retriever.get_relevant_documents(prompt)

        docs_enhanced = retriever.get_relevant_documents(enhanced_query)

        all_docs = docs_original + docs_enhanced
        unique_docs = []
        seen_content = set()

        for doc in all_docs:
            if doc.page_content not in seen_content:
                seen_content.add(doc.page_content)
                unique_docs.append(doc)

        doc_contents = []
        for doc in unique_docs[:7]:
            doc_contents.append(doc.page_content)

        context_text = "\n\n---\n\n".join(doc_contents)

        logger.info(f"Retrieved {len(unique_docs)} unique relevant documents")

        system_prompt = """
You are an expert in creating Manim animations. Use the context below from the Manim documentation to generate Python code using the Manim library to visualize mathematical concepts.

Follow these rules strictly:
1. Always include proper imports from manim.
2. Define a construct() method that builds the visualization step by step.
3. Use animations like Create(), Write(), etc.
4. Keep code simple, focused, and well-commented.
5. Do NOT include explanations or text outside Python code.
6. Include necessary imports like numpy as np if used.

IMPORTANT: You must use class Name as Scene.
Note can you give a typo inside the code actually for now i am testing the code so please make a type so manim command will fail in first run.


CONTEXT FROM MANIM DOCUMENTATION:
{context}

Here are examples of good Manim code structure:
    
    Example 1 - Boolean operations visualization:
    ```python
    from manim import *

    class BooleanOperations(Scene):
        def construct(self):
            ellipse1 = Ellipse(
                width=4.0, height=5.0, fill_opacity=0.5, color=BLUE, stroke_width=10
            ).move_to(LEFT)
            ellipse2 = ellipse1.copy().set_color(color=RED).move_to(RIGHT)
            bool_ops_text = MarkupText("<u>Boolean Operation</u>").next_to(ellipse1, UP * 3)
            ellipse_group = Group(bool_ops_text, ellipse1, ellipse2).move_to(LEFT * 3)
            self.play(FadeIn(ellipse_group))

            i = Intersection(ellipse1, ellipse2, color=GREEN, fill_opacity=0.5)
            self.play(i.animate.scale(0.25).move_to(RIGHT * 5 + UP * 2.5))
            intersection_text = Text("Intersection", font_size=23).next_to(i, UP)
            self.play(FadeIn(intersection_text))

            u = Union(ellipse1, ellipse2, color=ORANGE, fill_opacity=0.5)
            union_text = Text("Union", font_size=23)
            self.play(u.animate.scale(0.3).next_to(i, DOWN, buff=union_text.height * 3))
            union_text.next_to(u, UP)
            self.play(FadeIn(union_text))

            e = Exclusion(ellipse1, ellipse2, color=YELLOW, fill_opacity=0.5)
            exclusion_text = Text("Exclusion", font_size=23)
            self.play(e.animate.scale(0.3).next_to(u, DOWN, buff=exclusion_text.height * 3.5))
            exclusion_text.next_to(e, UP)
            self.play(FadeIn(exclusion_text))

            d = Difference(ellipse1, ellipse2, color=PINK, fill_opacity=0.5)
            difference_text = Text("Difference", font_size=23)
            self.play(d.animate.scale(0.3).next_to(u, LEFT, buff=difference_text.height * 3.5))
            difference_text.next_to(d, UP)
            self.play(FadeIn(difference_text))
    ```
    
    Example 2 - Following a graph with the camera:
    ```python
    from manim import *
    import numpy as np

    class FollowingGraphCamera(MovingCameraScene):
        def construct(self):
            self.camera.frame.save_state()

            # create the axes and the curve
            ax = Axes(x_range=[-1, 10], y_range=[-1, 10])
            graph = ax.plot(lambda x: np.sin(x), color=BLUE, x_range=[0, 3 * PI])

            # create dots based on the graph
            moving_dot = Dot(ax.i2gp(graph.t_min, graph), color=ORANGE)
            dot_1 = Dot(ax.i2gp(graph.t_min, graph))
            dot_2 = Dot(ax.i2gp(graph.t_max, graph))

            self.add(ax, graph, dot_1, dot_2, moving_dot)
            self.play(self.camera.frame.animate.scale(0.5).move_to(moving_dot))

            def update_curve(mob):
                mob.move_to(moving_dot.get_center())

            self.camera.frame.add_updater(update_curve)
            self.play(MoveAlongPath(moving_dot, graph, rate_func=linear))
            self.camera.frame.remove_updater(update_curve)

            self.play(Restore(self.camera.frame))
    ```
    
    Generate ONLY the Python code needed to visualize the concept described by the user.
    """

        human_prompt = (
            "Concept to visualize: {input}\n\nPlease provide only the Python code."
        )

        chat_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_prompt),
                HumanMessagePromptTemplate.from_template(human_prompt),
            ]
        )

        chat_prompt_value = chat_prompt.format_prompt(
            input=prompt, context=context_text
        )

        response = chat.invoke(
            input=chat_prompt_value.to_messages(),
        )

        logger.info(f"Generated response for prompt: {prompt[:30]}...")

        code = extract_python_code(response.content)
        return code

    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        return f"# Error generating code: {str(e)}"


def generate_code_with_history(conversation_history):
    """
    Generate improved Manim code using conversation history and error feedback.

    Args:
        conversation_history: List of HumanMessage and AIMessage instances

    Returns:
        str: Generated Python code
    """
    try:
        original_prompt = conversation_history[0].content

        doc_search = PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=embedding,
            pinecone_api_key=settings.PINECONE_API_KEY,
        )

        retriever = doc_search.as_retriever()
        docs = retriever.get_relevant_documents(original_prompt)

        doc_contents = [doc.page_content for doc in docs[:5]]
        context_text = "\n\n---\n\n".join(doc_contents)

        system_prompt = """
You are an expert in debugging and fixing Manim animations. Given a conversation history that includes:
1. The original concept request
2. Previous code generation attempts
3. Error messages from those attempts

Your task is to fix the code to make it work correctly.

Follow these rules strictly:
1. Always include proper imports from manim.
2. Define a construct() method that builds the visualization step by step.
3. Use animations like Create(), Write(), etc.
4. Keep code simple, focused, and well-commented.
5. Do NOT include explanations or text outside Python code.
6. Include necessary imports like numpy as np if used.
7. ALWAYS use 'class Scene' as the class name.
8. Carefully address the specific errors mentioned in the conversation history.

Here's some relevant Manim documentation that might help:
{context}

Based on the conversation history, generate corrected Python code. Return ONLY the code, no explanations or markdown.
"""

        chat_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_prompt),
                MessagesPlaceholder(variable_name="history"),
            ]
        )

        chat_prompt_value = chat_prompt.format_prompt(
            context=context_text, history=conversation_history
        )

        response = chat.invoke(
            input=chat_prompt_value.to_messages(),
        )

        logger.info("Generated improved code with error context")

        code = extract_python_code(response.content)
        return code

    except Exception as e:
        logger.error(f"Error generating improved code: {str(e)}")

        last_code = None
        for msg in reversed(conversation_history):
            if isinstance(msg, AIMessage):
                last_code = msg.content
                break

        if last_code:
            return last_code
        else:
            return f"# Error generating improved code: {str(e)}"
