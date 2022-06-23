from loguru import logger
from prettytable import PrettyTable

from parser.GLangParser import GLangParser


class PrettyParserOutput:
    def __init__(self, lang_parser: GLangParser):
        self.lang_parser = lang_parser

    def ids_table_output(self):
        logger.info("Ідентифікатори")

        tbl = PrettyTable(["Назва", "Індекс"])
        for name, indx in self.lang_parser.table_of_id.items():
            tbl.add_row([name, indx])

        logger.info(f"\n{tbl}")

    def postfix_table_output(self):
        logger.info("Постфіксний аналіз")

        tbl = PrettyTable(["Лексема", "Токен", "Тип"])
        for row in self.lang_parser.postfix_code:
            tbl.add_row([*row])

        logger.info(f"\n{tbl}")

