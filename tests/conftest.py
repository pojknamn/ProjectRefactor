from pytest import fixture
import libcst as cst

__author__ = 'pojk'


def return_cst(filepath: str) -> cst.Module:
    with open(filepath) as cl:
        return cst.parse_module(cl.read())


@fixture
def class_wo_start_requests():
    return return_cst('./classes/without_sr.py')


@fixture
def class_wo_init():
    return return_cst('./classes/without_init.py')


@fixture
def error_start_req():
    return return_cst('./classes/error_start_req.py')
