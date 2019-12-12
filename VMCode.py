DEFAULT_VM_LABELS = {'SP': 0, 'LCL': 1, 'ARG': 2, 'THIS': 3, 'THAT': 4, 'SCREEN': 16384, 'KBD': 24576}
DEFAULT_VM_LABELS.update({'R{}'.format(i): i for i in range(16)})


class VMCode:
    """
    Represents parsed assembly code ready for translation, and holds all the symbol info (i.e labels and
    variable names).
    """

    def __init__(self, VM_code, filename):
        """
        Creates an VMCode object with some lines of code and some (optional) symbol information.
        :param VM_code: A list of strings, each containing a line of assembly code, with no whitespaces and
                         no label decelerations.
        :param symbols: A dictionary containing symbol values.
                        Defaults to Default Hack assembly labels.
        """
        self.__VM_code = VM_code
        self.__filename = filename

    def get_vm_code(self):
        """
        Returns this object's list of assembly code lines
        :return: this object's list of assembly code lines
        """
        return self.__VM_code

    def get_filename(self):
        return self.__filename
