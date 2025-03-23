import mistune
import sys
import argparse

# ESC/POS Command Constants
ESC = "\x1B"
BOLD_ON = ESC + "E\x01"
BOLD_OFF = ESC + "E\x00"
UNDERLINE_ON = ESC + "-\x01"
UNDERLINE_OFF = ESC + "-\x00"
CENTER_ALIGN = ESC + "a\x01"
LEFT_ALIGN = ESC + "a\x00"
CUT = ESC + "i"

class EscposRenderer(mistune.HTMLRenderer):
    def __init__(self, debug=False):
        super().__init__()
        self.debug = debug

    def _debug_print(self, method_name, result):
        if self.debug:
            print(f"Debug: {method_name} -> {repr(result)}")

    def text(self, text):
        result = LEFT_ALIGN + text
        self._debug_print("text", result)
        return result

    def strong(self, text):
        result = BOLD_ON + text + BOLD_OFF
        self._debug_print("strong", result)
        return result

    def emphasis(self, text):
        result = UNDERLINE_ON + text + UNDERLINE_OFF
        self._debug_print("emphasis", result)
        return result

    def heading(self, text, level):
        result = CENTER_ALIGN + BOLD_ON + text.upper() + BOLD_OFF + "\n\n"
        self._debug_print("heading", result)
        return result

    def list_item(self, text):
        result = " - " + text + "\n"
        self._debug_print("list_item", result)
        return result
    
    def list(self, text, ordered, **attrs):
        result = text
        self._debug_print("list", result)
        return result

    def codespan(self, text):
        result = LEFT_ALIGN + "`" + text + "`\n"
        self._debug_print("codespan", result)
        return result

    def paragraph(self, text):
        result = LEFT_ALIGN + text + "\n\n"
        self._debug_print("paragraph", result)
        return result

    def blank_line(self):
        result = "-" * 48 + "\n"
        self._debug_print("block_hline", result)
        return result
    
    def thematic_break(self):
        result = "";
        self._debug_print("thematic_break", result)
        return result

   
def markdown_to_escpos(md_text, debug=False):
    """Convert Markdown text to ESC/POS escape sequences."""
    renderer = EscposRenderer(debug=debug)
    markdown = mistune.create_markdown(renderer=renderer)
    escpos_output = markdown(md_text)

    if debug:
        print(f"Debug: ESC/POS output:\n{repr(escpos_output)}")
        
        print("\n*** AST *** \n\n")
        ast = mistune.create_markdown(renderer='ast')
        print(ast(md_text))
        

    return escpos_output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Markdown text to ESC/POS escape sequences.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode to output recognized elements with ESC/POS codes")
    args = parser.parse_args()

    md_text = sys.stdin.read()
    
    escpos_text = markdown_to_escpos(md_text, debug=args.debug)
    
    if not args.debug:
        print(escpos_text)