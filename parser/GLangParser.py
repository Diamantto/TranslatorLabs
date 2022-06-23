from typing import List, Dict
from loguru import logger


class GLangParser:
    table_of_consts: Dict = {}
    postfix_code: List = []
    for_vars: List = []
    row_number: int = 1

    def __init__(self, table_of_symbols, table_of_id, table_of_consts, to_view=False):
        self.table_of_symbols = table_of_symbols
        self.len_table_of_symbols = len(self.table_of_symbols)
        self.table_of_consts = table_of_consts
        self.table_of_id = table_of_id
        self.to_view = to_view

    @staticmethod
    def fail_parse(error: str, *args):
        print("\033[31m")
        if error == 'eop':
            # row_number, lexeme, token = args
            row_number, = args
            print('GLangParser ERROR:'
                  f'\n\tНеочікуваний кінець програми - в таблиці символів немає запису з номером {row_number}.'
                  # f'\n\tОчікувалось - {row_number}'
                  )
            exit(1001)
        elif error == 'after_eop':
            print('GLangParser ERROR:'
                  f'\n\tНеочікуваіні лексеми за межами головної програми.'
                  # f'\n\tОчікувалось - {row_number}'
                  )
            exit(1002)
        elif error == 'tokens':
            line_number, expected_lex, expected_tok, actual_lex, actual_tok = args
            print(f'GLangParser ERROR:'
                  f'\n\tВ рядку {line_number} неочікуваний елемент ({expected_lex},{expected_tok}).'
                  f'\n\tОчікувався - ({actual_lex},{actual_tok}).')
            exit(1)
        elif error == 'not_expected':
            line_number, lex, tok, expected = args
            print(f'GLangParser ERROR:'
                  f'\n\tВ рядку {line_number} неочікуваний елемент ({lex},{tok}).'
                  f'\n\tОчікувався - {expected}.')
            exit(2)

    @staticmethod
    def warning_parse(warning: str, *args):
        print("\033[33m")
        if warning == 'no_effect':
            row_number, = args
            print('GLangParser Warning:'
                  f'\n\tВираз на рядку {row_number} не має ефекту.'
                  )
        print('\n\033[0m')

    def run(self):
        self.parse_program()
        print('\n\033[0m')

    def parse_program(self):
        try:
            self.parse_token('program', 'keyword')
            self.parse_token(F'{self.table_of_symbols[2][1]}', 'ident')

            self.parse_statements_list()

            if self.row_number < self.len_table_of_symbols:
                GLangParser.fail_parse('after_eop')
            else:
                self.parse_token('end.', 'keyword')
        except SystemExit as e:
            print("\033[31m")
            logger.info('GLangParser: Аварійне завершення програми з кодом {0}'.format(e))
            return False

        print("\033[32m")
        logger.info('GLangParser: Синтаксичний аналіз завершився успішно')
        return True

    def parse_token(self, lexeme, token):
        line_number, lex, tok = self.get_symbol()

        self.row_number += 1

        if lex == lexeme and tok == token:
            return True
        else:
            GLangParser.fail_parse('tokens', line_number, lex, tok, lexeme, token)
            return False

    def get_symbol(self):
        if self.row_number > self.len_table_of_symbols:
            GLangParser.fail_parse('eop', self.row_number)
        return self.table_of_symbols[self.row_number][0:-1]

    def parse_statements_list(self):
        while self.parse_statement():
            pass
        return True

    def parse_statement(self):
        line_number, lex, token = self.get_symbol()

        if lex == "var" and token == "keyword":
            self.parse_token("var", "keyword")
            while self.parse_var():
                self.parse_token(";", "op_end")
            return True

        elif token == "ident":
            self.postfix_code.append((lex, token, None))
            if self.to_view:
                self.config_to_print(lex)

            self.row_number += 1

            if self.get_symbol()[-1] == "assign_op":
                self.parse_assign()
            else:
                self.row_number -= 1
                self.parse_expression()
                GLangParser.warning_parse("no_effect", line_number)
            self.parse_token(";", "op_end")
            return True

        elif lex == "read" and token == "keyword":
            self.parse_read()
            self.parse_token(";", "op_end")
            return True

        elif lex == "write" and token == "keyword":
            self.parse_write()
            self.parse_token(";", "op_end")
            return True

        elif lex == "begin" and token == "keyword":
            self.parse_token("begin", "keyword")
            return True

        # elif lex == "?" and token == "question_op":
        #     self.parse_token("?", "question_op")
        #     return False

        elif lex == ":" and token == "colon_op":
            self.parse_token(":", "colon_op")
            return False

        elif lex == "if" and token == "keyword":
            self.parse_if()
            return True

        elif lex == "for" and token == "keyword":
            self.parse_for()
            return True

        elif lex == "end" and token == "keyword":
            self.parse_token('end', 'keyword')
            return False

        elif lex == "end." and token == "keyword":
            return False


        else:
            self.parse_expression()
            # self.parse_token(";", "op_end")
            GLangParser.warning_parse("no_effect", line_number)
            return True

    def parse_var(self):
        line_number, var, type = self.get_symbol()
        self.row_number += 1
        if type == "ident":
            line_number, lex, token = self.get_symbol()
            self.row_number += 1
            if lex == ":" and token == "colon_op":
                line_number, var_type, token = self.get_symbol()
                self.row_number += 1
                if token == "keyword" and var_type in ("integer", "boolean", "real"):
                    self.postfix_code.append((var, type, var_type))
                    return True
                else:
                    GLangParser.fail_parse(
                        "not_expected", line_number, var_type, token, "ідентифікатор (ident)"
                    )
        elif var == "begin" and type == "keyword":
            return False
        else:
            GLangParser.fail_parse(
                "not_expected", line_number, var, type, "ідентифікатор (ident)"
            )
        return False

    def config_to_print(self, lex):
        to_print = "\nTranslator step\n\tlexeme: %s\n\tsymbolsTable[%s]: %s\n\tpostfix_code %s\n"
        print(
            to_print
            % (
                lex,
                self.row_number,
                self.table_of_symbols[self.row_number],
                self.postfix_code,
            )
        )

    def parse_assign(self):
        if self.parse_token("=", "assign_op"):
            self.parse_expression()
            self.postfix_code.append(("=", "assign_op", None))
            if self.to_view:
                self.config_to_print("=")
            return True
        else:
            return False

    def parse_expression(self, required=False):
        # self.parse_arithm_expression()

        while self.parse_bool_expr():
            pass

        return True

    def parse_arithm_expression(self):
        self.parse_term()

        while True:
            line_number, lex, token = self.get_symbol()
            if token == "add_op":
                self.row_number += 1
                self.parse_term()
                self.postfix_code.append((lex, token, None))
                if self.to_view:
                    self.config_to_print(lex)
            else:
                break
        return True

    def parse_bool_expr(self, required=False):
        self.parse_arithm_expression()
        line_number, lex, token = self.get_symbol()
        if token in ("rel_op", "boolean"):
            self.row_number += 1
            self.parse_arithm_expression()
            self.postfix_code.append((lex, token, None))
            # self.row_number += 1
            return True

        elif required:
            GLangParser.fail_parse("not_expected", line_number, lex, token, required)

        else:
            return False

    def parse_term(self):
        self.parse_power()
        while True:
            line_number, lex, token = self.get_symbol()
            if token == "mult_op":
                self.row_number += 1
                self.parse_power()
                self.postfix_code.append((lex, token, None))
                if self.to_view:
                    self.config_to_print(lex)
            else:
                break
        return True

    def parse_power(self):
        self.parse_factor()
        while True:
            line_number, lex, token = self.get_symbol()
            if token == "pow_op":
                self.row_number += 1
                self.parse_factor()
                self.postfix_code.append((lex, token, None))
                if self.to_view:
                    self.config_to_print(lex)
            else:
                break
        return True

    def parse_factor(self):
        line_number, lex, token = self.get_symbol()

        if token in ("integer", "real", "boolean", "ident"):
            self.postfix_code.append((lex, token, None))
            if self.to_view:
                self.config_to_print(lex)
            self.row_number += 1

        elif lex == "(":
            self.row_number += 1
            self.parse_bool_expr()
            self.parse_token(")", "brackets_op")

        elif lex == "?" and token == "question_op":
            self.parse_token("?", "question_op")
            return False

        else:
            GLangParser.fail_parse(
                "not_expected",
                line_number,
                lex,
                token,
                "rel_op, integer, real, ident або '(' Expression ')'",
            )
        return True

    def parse_read(self):
        line_number, lex, token = self.get_symbol()
        self.row_number += 1

        self.parse_token("(", "brackets_op")
        self.parse_io_content(allow_arithm_expr=False)
        self.parse_token(")", "brackets_op")

    def parse_write(self):
        line_number, lex, token = self.get_symbol()
        self.row_number += 1

        self.parse_token("(", "brackets_op")
        self.parse_io_content()
        self.parse_token(")", "brackets_op")

    def parse_io_content(self, allow_arithm_expr=True):
        line_number, lex, token = self.get_symbol()

        if token in ("ident", "integer", "real", "boolean") and allow_arithm_expr:
            self.parse_arithm_expression()
        elif token == "ident":
            self.postfix_code.append((lex, token, None))
            self.row_number += 1
        else:
            GLangParser.fail_parse(
                "not_expected", line_number, lex, token, "ідентифікатор (ident)"
            )

        line_number, lex, token = self.get_symbol()
        if lex == ")" and token == "brackets_op":
            if allow_arithm_expr:
                self.postfix_code.append(("OUT", "out", None))
            else:
                self.postfix_code.append(("INPUT", "input", None))
            return True

        elif lex == "," and token == "comma":
            if allow_arithm_expr:
                self.postfix_code.append(("OUT", "out", None))
            else:
                self.postfix_code.append(("INPUT", "input", None))
            self.row_number += 1
            self.parse_io_content(allow_arithm_expr)

    def parse_if(self):
        _, lex, tok = self.get_symbol()
        if lex == 'if' and tok == 'keyword':
            self.row_number += 1
            self.parse_expression()
            # self.parse_token("?", "question_op")
            while self.parse_statement():
                pass
            # self.row_number -= 1
            self.parse_token(":", "colon_op")
            while self.parse_statement():
                pass
            return True
        else:
            return False

    def parse_for(self):
        _, lex, tok = self.get_symbol()
        if lex == 'for' and tok == 'keyword':
            self.row_number += 1
            self.parse_token("(", "brackets_op")
            self.row_number += 1
            self.parse_assign()
            self.parse_token(";", "op_end")
            self.row_number += 1
            self.parse_expression()
            self.parse_token(";", "op_end")
            self.parse_arithm_expression()
            self.parse_token(")", "brackets_op")
            while self.parse_statement():
                pass
            return True
        else:
            return False
