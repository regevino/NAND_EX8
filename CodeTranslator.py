ARITHMETIC_OPERATIONS = {'add': lambda x: ['M=M+D'],
                         'sub': lambda x: ['M=M-D'],
                         'neg': lambda x: ['A=A+1', 'M=-M', '@SP', 'M=M+1'],
                         'eq': lambda x: ['D=M-D', '@PUSH_TRUE{}'.format(x), 'D;JEQ', '@SP', 'A=M-1', 'M=0',
                                          '@END{}'.format(x), '0;JMP', '(PUSH_TRUE{})'.format(x),
                                          '@SP', 'A=M-1', 'M=-1', '(END{})'.format(x)],
                         'gt': lambda x: ['D=M-D', '@PUSH_TRUE{}'.format(x), 'D;JGT', '@SP', 'A=M-1', 'M=0',
                                          '@END{}'.format(x), '0;JMP', '(PUSH_TRUE{})'.format(x),
                                          '@SP', 'A=M-1', 'M=-1', '(END{})'.format(x)],
                         'lt': lambda x: ['D=D-M', '@PUSH_TRUE{}'.format(x), 'D;JGT', '@SP', 'A=M-1', 'M=0',
                                          '@END{}'.format(x), '0;JMP', '(PUSH_TRUE{})'.format(x),
                                          '@SP', 'A=M-1', 'M=-1', '(END{})'.format(x)],
                         'and': lambda x: ['M=M&D'],
                         'or': lambda x: ['M=M|D'],
                         'not': lambda x: ['A=A+1', 'M=!M', '@SP', 'M=M+1']}
FLOW_OPERATIONS = {'label': lambda file, func, label: ['({}{}${})'.format(file, func, label)],
                   'if-goto': lambda file, func, label: ['@SP', 'M=M-1', 'A=M', 'D=M',
                                                         '@{}{}${}'.format(file, func, label), 'D;JNE'],
                   'goto': lambda file, func, label: ['@{}{}${}'.format(file, func, label), '0;JMP']}


class CodeTranslator:
    """
    Represents an object that can translate VMCode objects into hack assembly code.
    """

    def __init__(self, parsed_VM_code, func_counter):
        """
        Create a translator object that can translate a specific VMCode object into HACK assembly code.
        :param parsed_VM_code: An VMCode object.
        """
        self.__VM_code = parsed_VM_code
        self.__filename = self.__VM_code.get_filename()
        self.__cur_func = ''
        self.__func_counter = func_counter
        self.SEGMENTS = {'argument': lambda x: ['@ARG', 'D=M', '@' + str(x), 'D=D+A', '@R13', 'M=D'],
                         'local': lambda x: ['@LCL', 'D=M', '@' + str(x), 'D=D+A', '@R13', 'M=D'],
                         'static': lambda x: ['@' + str(self.__filename) + str(x), 'D=A', '@R13', 'M=D'],
                         'constant': lambda x: ['@' + str(x), 'D=A', '@R14', 'M=D', 'D=A', '@R13', 'M=D'],
                         'this': lambda x: ['@THIS', 'D=M', '@' + str(x), 'D=D+A', '@R13', 'M=D'],
                         'that': lambda x: ['@THAT', 'D=M', '@' + str(x), 'D=D+A', '@R13', 'M=D'],
                         'pointer': lambda x: ['@R3', 'D=A', '@' + str(x), 'D=D+A', '@R13', 'M=D'],
                         'temp': lambda x: ['@R5', 'D=A', '@' + str(x), 'D=D+A', '@R13', 'M=D']}

    def translate(self):
        """
        Translate the VM code into Assembly code.
        :return: An array representing assembly code for HACK.
        """
        lines = []
        lines += self.__sys_init()
        for index, line in enumerate(self.__VM_code.get_vm_code()):
            lines += self.translate_instruction(line, index)
            index = len(lines) - 1
        return lines

    def translate_instruction(self, line, index):
        """
        Receives a line of vm code and translates command.
        :param index:
        :param line: line of code to translate.
        :return: the lines of translated assembly code.
        """
        lines = []
        lines.append("//Translating vm command: " + line)
        cmds = line.split()
        if cmds[0] == 'push' or cmds[0] == 'pop':
            lines += self.__memory_access(cmds)
        elif len(cmds) == 3 or cmds[0] == 'return':
            lines += self.__functions(cmds)
        elif len(cmds) == 2:
            lines += self.__program_flow(cmds)
        elif len(cmds) == 1:
            lines += self.__translate_arithmetic(cmds[0], index)
        return lines

    @staticmethod
    def __push():
        lines = []
        lines.append('@R13')
        lines.append('A=M')
        lines.append("D=M")
        lines.append('@SP')
        lines.append('M=M+1')
        lines.append('A=M-1')
        lines.append('M=D')
        return lines

    @staticmethod
    def __pop(save_result=True):
        lines = []
        lines.append('@SP')
        lines.append('M=M-1')
        lines.append('A=M')
        lines.append('D=M')
        if save_result:
            lines.append('@R13')
            lines.append('A=M')
            lines.append('M=D')
        return lines

    def __arithmetic(self, arithmetic_func, index):
        lines = []
        lines += self.__pop(save_result=False)
        lines.append('@SP')
        lines.append('A=M-1')
        index += len(lines)
        lines += arithmetic_func(index)
        return lines

    def __translate_arithmetic(self, line, index):
        return self.__arithmetic(ARITHMETIC_OPERATIONS[line], index)

    def __memory_access(self, split_line):
        lines = []
        lines += self.__set_address(split_line[1], split_line[2])
        if split_line[0] == 'pop':
            lines += self.__pop()
        elif split_line[0] == 'push':
            lines += self.__push()
        return lines

    def __set_address(self, segment_name, index):
        return self.SEGMENTS[segment_name](index)

    def __program_flow(self, line):
        return FLOW_OPERATIONS[line[0]](self.__filename, self.__cur_func, line[1])

    def __functions(self, cmds):
        if cmds[0] == 'function':
            return self.__declare_function(cmds[1:])
        if cmds[0] == 'call':
            return self.__call_function(cmds[1:])
        else:
            return self.__return()

    def __declare_function(self, cmds):
        file = self.__filename
        func = cmds[0]
        self.__cur_func = func
        num_locals = int(cmds[1])
        lines = ['({})'.format(func)]
        for i in range(num_locals):
            lines += ['@SP', 'M=M+1', 'A=M-1', 'M=0']
        return lines

    def __call_function(self, cmds):
        file = self.__filename
        func = cmds[0]
        num_args = cmds[1]
        if func in self.__func_counter.keys():
            self.__func_counter[func] += 1
        else:
            self.__func_counter[func] = 1
        index = self.__func_counter[func]

        return ['@{}$ret.{}'.format(func, index), 'D=A', '@SP', 'M=M+1', 'A=M-1', 'M=D',
                '@LCL', 'D=M', '@SP', 'M=M+1', 'A=M-1', 'M=D',
                '@ARG', 'D=M', '@SP', 'M=M+1', 'A=M-1', 'M=D',
                '@THIS', 'D=M', '@SP', 'M=M+1', 'A=M-1', 'M=D',
                '@THAT', 'D=M', '@SP', 'M=M+1', 'A=M-1', 'M=D',
                '@SP', 'D=M', '@5', 'D=D-A', '@' + num_args, 'D=D-A', '@ARG', 'M=D',
                '@SP', 'D=M', '@LCL', 'M=D',
                '@{}'.format(func), '0;JMP',
                '({}$ret.{})'.format(func, index)]

    def __return(self):
        return ['@LCL', 'D=M', '@R13', 'M=D',
                '@5', 'D=D-A', 'A=D', 'D=M', '@R14', 'M=D',
                '@SP', 'M=M-1', 'A=M', 'D=M', '@ARG', 'A=M', 'M=D',
                '@ARG', 'D=M+1', '@SP', 'M=D',
                '@R13', 'D=M', '@1', 'D=D-A', 'A=D', 'D=M', '@THAT', 'M=D',
                '@R13', 'D=M', '@2', 'D=D-A', 'A=D', 'D=M', '@THIS', 'M=D',
                '@R13', 'D=M', '@3', 'D=D-A', 'A=D', 'D=M', '@ARG', 'M=D',
                '@R13', 'D=M', '@4', 'D=D-A', 'A=D', 'D=M', '@LCL', 'M=D',
                '@R14', 'A=M', '0;JMP']

    def __sys_init(self):
        lines = ['@256', 'D=A', '@SP', 'M=D']
        return lines + self.__call_function(['Sys.init', '0'])

    def get_counter(self):
        return self.__func_counter
