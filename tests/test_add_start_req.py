import libcst as cst

from conf import logger
from helpers.helpers import check_start_requests
from helpers.transformers import ClassTransformer

logger.remove()


def test_update_start_requests(class_wo_start_requests):
    assert not check_start_requests(class_wo_start_requests)
    new_class = class_wo_start_requests.visit(ClassTransformer())
    assert check_start_requests(new_class)


def test_class_wo_init(class_wo_init):
    assert not check_start_requests(class_wo_init)
    new_class = class_wo_init.visit(ClassTransformer())
    assert not check_start_requests(new_class)


def test_error_start_req(error_start_req: cst.ClassDef):
    new_class = error_start_req.visit(ClassTransformer())
    assert error_start_req.code == new_class.code
