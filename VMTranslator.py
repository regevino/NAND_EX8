import os
import sys

from CodeTranslator import CodeTranslator
from AssemblyWriter import AssemblyWriter
from Parser import Parser

if __name__ == '__main__':
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        exit(1)
    vm_file_path = sys.argv[1]

    files_list = [os.path.abspath(vm_file_path)]
    path_to_dir = ''
    out_file = files_list[0][:-3] + '.asm'

    if os.path.isdir(vm_file_path):
        files_list = os.listdir(vm_file_path)
        path_to_dir = os.path.abspath(vm_file_path)
        out_file = os.path.join(path_to_dir, os.path.basename(path_to_dir) + '.asm')

    asm_file_translations = []
    for file in filter(lambda x: x[-3:] == '.vm', files_list):
        file = os.path.join(path_to_dir, file)
        file_parser = Parser(file)
        parsed_code = file_parser.parse()
        code_translator = CodeTranslator(parsed_code)
        assembly_code = code_translator.translate()
        asm_file_translations.append(assembly_code)

    asm_writer = AssemblyWriter(asm_file_translations, out_file)
    asm_writer.write_out()
