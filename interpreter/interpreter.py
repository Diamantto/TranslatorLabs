import traceback
from loguru import logger

from interpreter.constants import type_mapping
from interpreter.stack import Stack
from prettytable import PrettyTable


class GLangInterpreter:
    operator_mapping = {
        '+': '+', '-': '-', '*': '*', '/': '/', '^': '**', '=': '=',
        '<': '<', '<=': '<=', '==': '==', '!=': '!=', '>=': '>=', '>': '>',
    }

    __header_for_errors = 'GLangInterpreter Error:'
    run_time_errors = {
        'mismatches_types': ('%s\n\tТипи операндів відрізняються: %s %s %s.', 1),
        'undefined_var': ('%s\n\tНевідома змінна \'%s\'.', 2),
        'zero_division': ('%s\n\tДілення на нуль: %s %s %s.', 3),
        'invalid_operand_types': ('%s\n\tНевалідний тип одного або декількох операндів: %s %s %s.', 4),
        'nullable': ('%s\n\tНевизначена зміна \'%s\' не може використовуватись в операціях.', 5),
        'print_error': ('%s\n\tНевизначена зміна \'%s\' не може використовуватись в операціях.', 5),
        'invalid_operator': ('%s\n\tНевідомий оператор %s', 322),
        'empty_label': ('%s\n\tПусте значення мітки', 7),
        'invalid_value': ('%s\n\tНевідомий тип даних: \'%s\'%s', 8)
    }

    def __init__(self, postfix_code, table_of_ids, table_of_consts, to_view=False):
        self.postfix_code = postfix_code
        self.table_of_ids = table_of_ids
        self.table_of_consts = table_of_consts
        self.stack = Stack()
        self.final_msg = []
        self.to_view = to_view
        self.instr_num = 0
        self.success = True

    def what_step_to_print(self, step, lex, tok):
        # pass
        print('\nКрок інтерпретації: {0}'.format(step))
        if tok in ('int', 'real'):
            print(f'Лексема: {(lex, tok)} у таблиці констант: {lex}:{self.table_of_consts[lex]}')
        elif tok in ('ident',):
            # pass
            print(f'Лексема: {(lex, tok)} у таблиці ідентифікаторів: {lex}:{self.table_of_ids[lex]}')
        else:
            print(f'Лексема: {(lex, tok)}')

        print(f'postfixCode={self.postfix_code}')
        print(self.stack)

    def run(self):
        self.success = self.__postfixProc()

    def __postfixProc(self):
        cycles_numb = 0
        try:
            while self.instr_num < len(self.postfix_code) and cycles_numb < 500:
                cycles_numb += 1
                lex, tok, var_type = self.postfix_code[self.instr_num]
                if tok in ('integer', 'real', 'boolean', 'ident'):
                    self.stack.push((lex, tok))
                    if tok == 'ident' and var_type:
                        # print(var_type,lex, tok)
                        # print(self.table_of_ids)
                        #  print(self.table_of_ids[lex])
                        self.table_of_ids[lex] = (
                            self.table_of_ids[lex][0],
                            var_type,
                            self.table_of_ids[lex][2]
                        )
                    next_num = self.instr_num + 1
                elif tok == 'out':
                    self.__print_data()
                    next_num = self.instr_num + 1
                elif tok == 'input':
                    self.__input_data()
                    next_num = self.instr_num + 1
                else:
                    self.__doSmth(lex, tok)
                    next_num = self.instr_num + 1
                if self.to_view:
                    self.what_step_to_print(self.instr_num + 1, lex, tok)
                self.instr_num = next_num
                if cycles_numb == 500:
                    self.final_msg.append("ПОМИЛКА! ЗАВЕРШЕННЯ ПРОГРАМИ ЧЕРЕЗ ДУЖЕ ВЕЛИКУ КІЛЬКІСТЬ ОПЕРАЦІЙ!!!")
        except SystemExit as e:
            print("\033[31m")
            print('GLangInterpreter: Аварійне завершення програми з кодом {0}'.format(e))
            print('\n\033[0m')
            return False
        except Exception as e:
            print(e)
            print(traceback.format_exc())
        else:
            print("\033[32m", end='')
            print('GLangInterpreter: Інтерпретатор завершив роботу успішно')
            print('\n\033[0m', end='')
            return True

    def __doSmth(self, lex, tok):
        if lex == '=' and tok == 'assign_op':
            lex_right, tok_right = self.stack.pop()
            value_right, type_right = self.__check_if_declared(tok_right, lex_right)
            lex_left, tok_left = self.stack.pop()
            _, type_left = self.__check_if_declared(tok_right, lex_right)

            if tok_left == 'ident':
                _type = self.table_of_ids[lex_left][1]
                if (_type, type_right) in (
                ('integer', 'real'), ('real', 'integer'), ('real', 'boolean'), ('integer', 'boolean'),
                ('boolean', 'integer'), ('boolean', 'real')):
                    GLangInterpreter.fail_run_time('mismatches_types', lex_left, lex, value_right)
            else:
                _type = type_left

            self.table_of_ids[lex_left] = (
                self.table_of_ids[lex_left][0],
                _type,
                # eval(f"{type_mapping[_type]}({value_right})")
                type_mapping[_type](value_right)
            )
        elif tok in ('add_op', 'mult_op', 'pow_op'):
            lex_right, tok_right = self.stack.pop()
            lex_left, tok_left = self.stack.pop()

            if (tok_right, tok_left) in (('integer', 'real'), ('real', 'integer')):
                GLangInterpreter.fail_run_time('mismatches_types', lex_left, lex, lex_right)

            self.__process_operator((lex_left, tok_left), lex, (lex_right, tok_right))

        elif tok in ('rel_op', 'bool_op'):
            lex_right, tok_right = self.stack.pop()
            lex_left, tok_left = self.stack.pop()

            if tok == 'bool_op' and (tok_right, tok_left) != ('boolean', 'boolean'):
                # add error
                GLangInterpreter.fail_run_time('invalid_operand_types', lex_left, lex, lex_right)

            if tok == 'rel_op':
                if lex not in ('==', '!=') and not all((tok in ('integer', 'real', 'ident') for tok
                                                        in (tok_right, tok_left))):
                    GLangInterpreter.fail_run_time('invalid_operand_types', lex_left, lex, lex_right)
            self.__process_operator((lex_left, tok_left), lex, (lex_right, tok_right))

    def __process_operator(self, left, lex, right):
        lex_left, tok_left = left
        lex_right, tok_right = right

        value_left, type_left = self.__check_if_declared(tok_left, lex_left)
        value_right, type_right = self.__check_if_declared(tok_right, lex_right)

        self.__run_operator((lex_left, type_left, value_left), lex, (lex_right, type_right, value_right))

    def __check_if_declared(self, token, lexeme):
        lexeme = str(lexeme)
        if token == 'ident':
            if GLangInterpreter.__is_undefined(self.table_of_ids[lexeme][1]):
                GLangInterpreter.fail_run_time('undefined_var', lexeme)
            return self.table_of_ids[lexeme][2], self.table_of_ids[lexeme][1]

        else:
            return self.table_of_consts[lexeme][2], self.table_of_consts[lexeme][1]

    def __run_operator(self, left, lex, right):
        lex_left, type_left, value_left = left
        lex_right, type_right, value_right = right

        if self.table_of_ids.get(lex_left, None) and GLangInterpreter.__is_nullable(value_left):
            GLangInterpreter.fail_run_time('nullable', lex_left)
        if self.table_of_ids.get(lex_right, None) and GLangInterpreter.__is_nullable(value_right):
            GLangInterpreter.fail_run_time('nullable', lex_right)

        if operator := GLangInterpreter.operator_mapping.get(lex, None):
            try:
                # print(f"CALC: {value_left} {operator} {value_right}")
                # calc_result = eval(f"{value_left} {operator} {value_right}")
                calc_result = eval(f"{value_left} {operator} {value_right}")
            except ZeroDivisionError:
                GLangInterpreter.fail_run_time('zero_division', value_left, operator, value_right)
            else:
                if lex == "/" and type_right:
                    calc_result = int(calc_result)
                if lex in ('<', '<=', '==', '!=', '>=', '>',):
                    _type = 'boolean'
                else:
                    _type = type_left
                self.stack.push((calc_result, _type))
                self.push_to_table_of_consts(_type, calc_result)

        else:
            GLangInterpreter.fail_run_time('invalid_operator', operator)

    def push_to_table_of_consts(self, token, value):
        if not self.table_of_consts.get(str(value), None):
            index = len(self.table_of_consts) + 1
            self.table_of_consts[str(value)] = (index, token, value)

    def __print_data(self):
        try:
            lex, tok = self.stack.pop()  # CHECK
            _, _ = self.__check_if_declared(tok, lex)
            if tok == 'ident':
                if to_print := self.table_of_ids.get(lex):
                    self.final_msg.append(to_print[-1])
            elif tok == 'boolean':
                lex = str(lex).lower()
                self.final_msg.append(lex)
            else:
                self.final_msg.append(lex)
        except Exception as e:
            GLangInterpreter.fail_run_time('print_error')

    def __input_data(self):
        lex, tok = self.stack.pop()
        _, var_type = self.__check_if_declared(tok, lex)
        logger.info('GLang просить внести деяке значення: ')
        temp = input()
        try:
            typed_temp = type_mapping[var_type](temp)
        except Exception:
            GLangInterpreter.fail_run_time('invalid_value', lex, temp)
        else:
            self.table_of_ids[lex] = (
                self.table_of_ids[lex][0],
                var_type,
                typed_temp
            )

    def _pretty_pr_table_id(self):
        print("Таблиця ідентифікаторів")
        tbl = PrettyTable(["Назва", "Індекс", "Value"])
        for name, indx in self.table_of_ids.items():
            tbl.add_row([name, indx])
        print(tbl)

    @staticmethod
    def __is_undefined(variable_type):
        return variable_type == "undefined"

    @staticmethod
    def __is_nullable(variable_value):
        return variable_value == 'null'

    @staticmethod
    def fail_run_time(error, *args):
        print("\033[31m")
        error_msg, error_code = GLangInterpreter.run_time_errors.get(error, (None, None))
        print(error_msg % (GLangInterpreter.__header_for_errors, *args))
        print('\n\033[0m')
        exit(error_code)

    def pretty_pr_table_id(self):
        print("Таблиця ідентифікаторів")
        tbl = PrettyTable(["Name", "Index", "Value"])

        for indx, val in self.table_of_ids.items():
            tbl.add_row([indx, val[0], val[1]])
        print(tbl)
