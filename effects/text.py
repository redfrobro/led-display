"""Text effect - Display scrolling or static text on the matrix."""

import time
import os
import logging

from .base import effect
from .utils import hsv_to_rgb

logger = logging.getLogger('led-demos')


@effect('text', 'Text Display',
        category='special',
        text=(None, "Text to display (None = load from config)"),
        font_name=('6x10.bdf', "BDF font file from fonts/ folder"),
        scroll_speed=(2.0, "Scroll speed in pixels/sec (0 = static)"),
        color_hue=(200, "Text color hue 0-360"))
def text_display(ctx, duration=0, frequency=5, text=None, font_name=None,
                 scroll_speed=None, color_hue=None, check_interrupt=None,
                 config_loader=None, config_saver=None, project_dir=None, **kwargs):
    """Display scrolling or static text on the matrix.

    Note: duration is respected (0 = run forever, default: 0). Frequency parameter is ignored.

    Args:
        ctx: EffectContext with matrix reference
        duration: How long to run (0 = forever)
        text: Text to display (if None, loads from config)
        font_name: BDF font file from fonts/ folder (if None, loads from config)
        scroll_speed: Pixels per second for scrolling (0 = static centered)
        color_hue: Color hue 0-360 for text
        config_loader: Optional function to load config (returns dict with text, font_name, scroll_speed, color_hue)
        config_saver: Optional function to save individual config options (key, value)
        project_dir: Project directory for finding fonts (defaults to parent of effects/)
    """
    # Import graphics from rgbmatrix (required for fonts)
    try:
        from rgbmatrix import graphics
    except ImportError:
        logger.error("Could not import graphics from rgbmatrix")
        return

    # Default config values
    defaults = {
        'text': 'Hello World',
        'font_name': '6x10.bdf',
        'color_hue': 200,
        'scroll_speed': 2.0
    }

    # Load config if loader provided and values are None
    config = defaults.copy()
    if config_loader is not None:
        try:
            loaded = config_loader()
            config.update(loaded)
        except Exception as e:
            logger.warning("Failed to load text effect config: %s" % e)

    # Use provided values or fall back to config
    if text is None:
        text = config['text']
    elif config_saver is not None:
        config_saver('text', text)

    if font_name is None:
        font_name = config['font_name']
    elif config_saver is not None:
        config_saver('font_name', font_name)

    if scroll_speed is None:
        scroll_speed = config['scroll_speed']
    elif config_saver is not None:
        config_saver('scroll_speed', scroll_speed)

    if color_hue is None:
        color_hue = config['color_hue']
    elif config_saver is not None:
        config_saver('color_hue', color_hue)

    # Determine project directory for fonts
    if project_dir is None:
        # Default: effects/ is a subdirectory, so parent is project root
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load font using rgbmatrix graphics
    font_path = os.path.join(project_dir, 'fonts', font_name)
    logger.info("Font path: %s, exists: %s" % (font_path, os.path.exists(font_path)))

    font = graphics.Font()
    try:
        font.LoadFont(font_path)
        logger.info("Loaded BDF font: %s" % font_name)
        if hasattr(font, 'height'):
            logger.info("Font height: %s, baseline: %s" % (font.height, font.baseline if hasattr(font, 'baseline') else 'N/A'))
    except Exception as e:
        logger.error("Failed to load BDF font %s: %s" % (font_name, e))
        # Try to load default font as fallback
        default_font = '6x10.bdf'
        default_path = os.path.join(project_dir, 'fonts', default_font)
        logger.info("Trying fallback font: %s" % default_font)
        try:
            font.LoadFont(default_path)
            logger.info("Loaded fallback font: %s" % default_font)
        except Exception as e2:
            logger.error("Failed to load fallback font %s: %s" % (default_font, e2))
            return

    # Convert color from HSV to RGB
    r, g, b = hsv_to_rgb(color_hue, 1.0, 1.0)
    text_color = graphics.Color(r, g, b)

    # Create a canvas for drawing
    canvas = ctx.matrix.CreateFrameCanvas()

    # Helper function to draw text with tight spacing (1 pixel between characters)
    def draw_text_tight(canvas, font, x, y, color, text_str):
        """Draw text with 1 pixel spacing between characters, returns total width drawn"""
        total_width = 0
        spacing_reduce = 1
        for i, char in enumerate(text_str):
            char_width = graphics.DrawText(canvas, font, x + total_width, y, color, char)
            if i < len(text_str) - 1 and char_width > spacing_reduce:
                total_width += char_width - spacing_reduce
            else:
                total_width += char_width
        return total_width

    # Helper to measure text width with tight spacing (without drawing)
    def measure_text_tight(font, text_str):
        """Measure text width with 1 pixel spacing between characters"""
        temp_canvas = ctx.matrix.CreateFrameCanvas()
        total_width = 0
        spacing_reduce = 1
        for i, char in enumerate(text_str):
            char_width = graphics.DrawText(temp_canvas, font, 0, 0, graphics.Color(0, 0, 0), char)
            if i < len(text_str) - 1 and char_width > spacing_reduce:
                total_width += char_width - spacing_reduce
            else:
                total_width += char_width
        return total_width

    # Split text into lines
    lines = text.split('\n') if '\n' in text else [text]

    # Font metrics
    if hasattr(font, 'height'):
        font_height = font.height
        baseline = font.baseline if hasattr(font, 'baseline') else font_height
    else:
        font_height = 8
        baseline = 8

    line_spacing = font_height + 1
    total_height = len(lines) * font_height + (len(lines) - 1)
    start_y = (ctx.rows - total_height) // 2 + baseline

    start_time = time.time()

    if len(lines) > 1:
        # Multi-line static mode: center each line horizontally, stack vertically
        line_widths = [measure_text_tight(font, line) for line in lines]
        max_width = max(line_widths) if line_widths else ctx.cols

        if scroll_speed > 0 and max_width > ctx.cols:
            # Scroll all lines together at the same horizontal offset
            total_scroll_width = max_width + ctx.cols
            scroll_offset = 0
            while True:
                if ctx.check_interrupt():
                    return
                if duration > 0 and time.time() - start_time >= duration:
                    return
                canvas.Clear()
                for i, (line, lw) in enumerate(zip(lines, line_widths)):
                    x_pos = ctx.cols - scroll_offset
                    y_pos = start_y + i * line_spacing
                    draw_text_tight(canvas, font, x_pos, y_pos, text_color, line)
                canvas = ctx.matrix.SwapOnVSync(canvas)
                scroll_offset += scroll_speed * 0.05
                if scroll_offset > total_scroll_width:
                    scroll_offset = 0
                time.sleep(0.05)
        else:
            # Static multi-line: center each line individually
            canvas.Clear()
            for i, (line, lw) in enumerate(zip(lines, line_widths)):
                x_pos = max(0, (ctx.cols - lw) // 2)
                y_pos = start_y + i * line_spacing
                draw_text_tight(canvas, font, x_pos, y_pos, text_color, line)
            canvas = ctx.matrix.SwapOnVSync(canvas)
            while True:
                if ctx.check_interrupt():
                    return
                if duration > 0 and time.time() - start_time >= duration:
                    return
                time.sleep(0.1)
    else:
        # Single-line mode
        text_width = measure_text_tight(font, lines[0])
        y_pos = start_y
        needs_scroll = text_width > ctx.cols and scroll_speed > 0

        if needs_scroll:
            total_scroll_width = text_width + ctx.cols
            scroll_offset = 0
            while True:
                if ctx.check_interrupt():
                    return
                if duration > 0 and time.time() - start_time >= duration:
                    return
                canvas.Clear()
                x_pos = ctx.cols - scroll_offset
                draw_text_tight(canvas, font, x_pos, y_pos, text_color, lines[0])
                canvas = ctx.matrix.SwapOnVSync(canvas)
                scroll_offset += scroll_speed * 0.05
                if scroll_offset > total_scroll_width:
                    scroll_offset = 0
                time.sleep(0.05)
        else:
            x_pos = max(0, (ctx.cols - text_width) // 2)
            canvas.Clear()
            draw_text_tight(canvas, font, x_pos, y_pos, text_color, lines[0])
            canvas = ctx.matrix.SwapOnVSync(canvas)
            while True:
                if ctx.check_interrupt():
                    return
                if duration > 0 and time.time() - start_time >= duration:
                    return
                time.sleep(0.1)
