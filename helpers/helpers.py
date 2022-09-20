import os
import time
from functools import wraps

import libcst as cst
from libcst import CSTVisitor
from libcst import matchers as m
from .transformers import ClassTransformer

from conf import logger, PROJECT_FOLDER


def get_cst_from_file(file_path):
    with open(file_path) as code:
        code = code.read()
    tree = cst.parse_module(code)
    return tree


def elapsed_time(func):
    @wraps(func)
    def inner(*args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        total_duration = time.time() - start_time
        logger.info(total_duration)

    return inner


def get_files(debug):
    workdir = os.path.abspath(PROJECT_FOLDER)
    result_dir = workdir
    if debug:
        workdir = os.path.join(os.getcwd(), 'test_files')
        result_dir = os.path.join(workdir, 'results')
    files = os.listdir(workdir)
    files = [file for file in files if file.endswith('.py')]
    total_count = len(files)
    files = [
        "frisco_pl.py"
    ]
    return files, result_dir, total_count, workdir


def refactor(files, result_dir, total_count, workdir):
    for filenum, filename in enumerate(files, 1):
        logger.info(f'{filenum}/{total_count}: started - {filename}')
        file_path = os.path.join(workdir, filename)
        tree = get_cst_from_file(file_path)
        # добавляем старт реквестс туда, где их не было
        with_start_req = tree.visit(ClassTransformer())
        new_file_path = os.path.join(result_dir, filename)
        with open(new_file_path, "w") as new_file:
            new_file.write(with_start_req.code)


class StartRequestVisitor(CSTVisitor):

    def __init__(self, have_start_req=None):
        self.have_start_req = have_start_req

    def on_leave(self, original_node: "CSTNode") -> bool:
        if m.matches(original_node, m.FunctionDef(name=m.Name('start_requests'))):
            self.have_start_req.append('Here')


def check_start_requests(cst_class: cst.ClassDef) -> bool:
    to_check = []
    cst_class.visit(StartRequestVisitor(to_check))
    if to_check:
        return True
    return False
