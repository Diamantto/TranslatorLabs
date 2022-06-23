from loguru import logger

from prettytable import PrettyTable

from interpreter.constants import type_mapping
from lexer.domain import LexerData


class GLangLexer:
    table_of_id: dict = {}
    table_of_const: dict = {}
    table_of_symb: dict = {}

    def __init__(self, lang_code, lexer_data: LexerData):
        self.program_code = lang_code + " "
        self.len_of_code = len(self.program_code)
        # Tables
        self.table_of_symbols = PrettyTable(["#", "Лексема", "Токен", "Індекс"])

        self.table_of_language_tokens = lexer_data.table_of_language_tokens
        self.table_ident_float_int = lexer_data.table_ident_float_int
        self.classes = lexer_data.classes
        self.stf = lexer_data.stf
        self.states = lexer_data.states
        self.errors_states = lexer_data.errors_states
        self.lastClass = ""
        # Current State
        self.state = self.states["initial"][0]

        # Needed variables
        self.num_line = 1
        self.num_char = 0
        self.char = ""
        self.lexeme = ""

    def start(self):
        try:
            while self.num_char < self.len_of_code:
                self.char = self._next_char()  # read next char
                self.state = self._next_state(
                    self.state, self._class_of_char(self.char)
                )
                if self._is_initial_state(self.state):
                    self.lexeme = ""
                elif self._is_final_state(self.state):
                    self.processing()
                else:
                    self.lexeme += self.char
            logger.info("GLangLexer:  Лексичний аналіз завершено успішно")
        except SystemExit as err:
            logger.info("GLangLexer: Аварійне завершення програми з кодом {}", err)

    def processing(self):

        if self.state in self.states["newLine"]:
            self.num_line += 1
            self.state = self.states["initial"][0]

        elif self.state in (self.states["const"] + self.states["identifier"]):
            token = self._get_token(self.state, self.lexeme)
            if token != "keyword":
                index = self._get_index()
                self.table_of_symbols.add_row([self.num_line, self.lexeme, token, index])
                self.table_of_symb[len(self.table_of_symb) + 1] = (
                    self.num_line,
                    self.lexeme,
                    token,
                    index,
                )
            else:
                self.table_of_symbols.add_row([self.num_line, self.lexeme, token, ""])
                self.table_of_symb[len(self.table_of_symb) + 1] = (
                    self.num_line,
                    self.lexeme,
                    token,
                    "",
                )

            self.lexeme = ""
            self.state = self.states["initial"][0]
            self._put_char_back()

        elif self.state in self.states["operators"]:
            if not self.lexeme or self.state in self.states["double_operators"]:
                self.lexeme += self.char
            token = self._get_token(self.state, self.lexeme)
            self.table_of_symbols.add_row([self.num_line, self.lexeme, token, ""])
            self.table_of_symb[len(self.table_of_symb) + 1] = (
                self.num_line,
                self.lexeme,
                token,
                "",
            )
            if self.state in self.states["star"]:
                self._put_char_back()
            self.lexeme = ""
            self.state = self.states["initial"][0]

        elif self.state in self.states["errors"]:
            self.fail()

    def fail(self):
        for num, text in self.errors_states.items():
            if self.state == num:
                logger.error(text, self.num_line, self.char)
                exit(num)

    def _get_index(self):
        if self.state in self.states["const"] or self.lexeme in ("true", "false"):
            return self._get_set_id(self.state, self.lexeme, self.table_of_const)
        elif self.state in self.states["identifier"]:
            return self._get_set_id(self.state, self.lexeme, self.table_of_id)

    def _next_char(self):
        char = self.program_code[self.num_char]
        self.num_char += 1
        return char

    def _put_char_back(self):
        self.num_char += -1

    def _get_token(self, state, lexeme):
        try:
            return self.table_of_language_tokens[lexeme]
        except KeyError:
            return self.table_ident_float_int[state]

    def _is_initial_state(self, state):
        return state in self.states["initial"]

    def _is_final_state(self, state):
        return state in self.states["final"]

    def _next_state(self, state, cls):
        try:
            return self.stf[(state, cls)]
        except KeyError:
            return self.stf[(state, "other")]

    def _class_of_char(self, char):
        for key, value in self.classes.items():
            if char in value:
                if key == "Operators":
                    return char
                elif self.lastClass == "Digit" and char == "e":
                    return "ExpOp"
                else:
                    self.lastClass = key
                    return key
        return "Цей символ не входить в жодний клас"

    def _get_set_id(self, state, lexeme, table):
        index = table.get(lexeme)
        if not index:
            index = len(table) + 1
            if (token := self._get_token(state, lexeme)) == "ident":
                token = "undefined"
            table[lexeme] = (index, token)

            if (token := self._get_token(state, lexeme)) == "label":
                token = "undefined"
            table[lexeme] = (index, token)

            if lexeme in ("true", "false"):
                table[lexeme] += (type_mapping[lexeme],)
            elif state in (self.states["identifier"]):
                table[lexeme] += ("null",)
            else:
                table[lexeme] += (type_mapping[token](lexeme),)
        return index
