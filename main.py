from time import sleep
from interpreter.interpreter import GLangInterpreter
from lexer.constants import (
    classes,
    errors_states,
    states,
    stf,
    table_ident_float_int,
    table_of_language_tokens,
)
from lexer.domain import LexerData
from lexer.GLangLexer import GLangLexer
from parser.GLangParser import GLangParser

from lexer.pretty_table_output import PrettyLexerOutput
from pretty_table_output import PrettyParserOutput

if __name__ == "__main__":
    print()
    with open("my_lang.glang", "r") as f:
        source_code = f.read()
    lexer_data = LexerData(
        table_of_language_tokens=table_of_language_tokens,
        table_ident_float_int=table_ident_float_int,
        classes=classes,
        stf=stf,
        errors_states=errors_states,
        states=states,
    )
    lexer = GLangLexer(
        source_code, lexer_data
    )
    lexer.start()
    pretty_lexer_output = PrettyLexerOutput(lang_lexer=lexer)
    pretty_lexer_output.symbols_table_output()
    pretty_lexer_output.const_table_output()
    pretty_lexer_output.ids_table_output()
    sleep(0.5)

    parser = GLangParser(lexer.table_of_symb, lexer.table_of_id, lexer.table_of_const)
    parser.run()
    pretty_parser_output = PrettyParserOutput(lang_parser=parser)
    pretty_parser_output.ids_table_output()
    pretty_parser_output.postfix_table_output()
    sleep(0.5)

    translator = GLangInterpreter(parser.postfix_code, parser.table_of_id, lexer.table_of_const, to_view=False)
    print(parser.postfix_code)
    translator.run()
    if translator.success:
        print("МОВА ПРОГРАМУВАННЯ GLang ХОЧЕ НАДРУКУВАТИ:")
        for val in translator.final_msg:
            print(val)
        translator.pretty_pr_table_id()
        print(translator.table_of_consts.items())


