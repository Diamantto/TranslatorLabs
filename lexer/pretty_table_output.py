from loguru import logger
from prettytable import PrettyTable

from lexer.GLangLexer import GLangLexer


class PrettyLexerOutput:
    def __init__(self, lang_lexer: GLangLexer):
        self.lang_lexer = lang_lexer

    def ids_table_output(self):
        logger.info("Ідентифікатори")

        tbl = PrettyTable(["Назва", "Індекс"])
        for name, indx in self.lang_lexer.table_of_id.items():
            tbl.add_row([name, indx])

        logger.info(f"\n{tbl}")

    def const_table_output(self):
        logger.info("Константи")

        tbl = PrettyTable(["Константа", "Індекс"])
        for cnst, indx in self.lang_lexer.table_of_const.items():
            tbl.add_row([cnst, indx])

        logger.info(f"\n{tbl}")

    def symbols_table_output(self):
        logger.info("Cимволи")

        logger.info(f"\n{self.lang_lexer.table_of_symbols}")
