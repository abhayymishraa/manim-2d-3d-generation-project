import google.generativeai as genai
import re
import logging
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash")


def extract_python_code(text: str) -> str:
    """Extract Python code from text that might contain markdown code blocks."""
    # Try to extract code from markdown code blocks
    code_pattern = re.compile(r"```(?:python)?\s*([\s\S]*?)\s*```")
    matches = code_pattern.findall(text)

    if matches:
        return matches[0]

    return text


def generate_manim_code(prompt: str) -> str:
    """Generate Manim code using Gemini model with template context."""

    context = """
    You are an expert in creating Manim animations. I need Python code using the Manim library to visualize mathematical concepts.
    
    Please follow these guidelines:
    1. Always include the proper imports from manim
    2. Create a Scene or ThreeDScene class that inherits from the appropriate Manim class
    3. The class should always be named 'Scene' for consistency
    4. Define a construct method that builds the visualization step by step
    5. Use appropriate animations like Create(), Write(), etc.
    6. Keep the code simple, focused, and well-commented
    7. Don't include any explanations or text outside of the Python code
    8. Always include any necessary imports like numpy (as np) if you use them
    
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
    
    Example 2 - 3D visualization:
    ```python
    from manim import *
    import numpy as np
    
    class Scene(ThreeDScene):
        def construct(self):
            # Set up 3D axes
            axes = ThreeDAxes()
            
            # Create a sphere
            sphere = Sphere(radius=1, resolution=(20, 20))
            sphere.set_color(BLUE)
            
            # Set up the camera
            self.set_camera_orientation(phi=75 * DEGREES, theta=30 * DEGREES)
            
            # Add to scene with animation
            self.play(Create(axes))
            self.play(Create(sphere))
            self.begin_ambient_camera_rotation(rate=0.2)
            self.wait(3)
    ```
    
    Example 3 - Following a graph with the camera:
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
    
    Please generate ONLY the Python code needed to visualize the concept I'm about to describe.
    """

    full_prompt = f"{context}\n\nConcept to visualize: {prompt}\n\nPlease provide only the Python code without any explanation:"

    try:
        response = model.generate_content(full_prompt)
        code = extract_python_code(response.text.strip())
        logger.info(f"Generated code for: {prompt[:30]}...")
        return code
    except Exception as e:
        logger.error(f"Error generating code with Gemini: {str(e)}")
        return f"# Error generating code: {str(e)}"
