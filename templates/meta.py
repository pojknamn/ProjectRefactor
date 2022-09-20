import libcst as cst
from conf import PROJECT_REFACTOR_PATH
start_url_meta = cst.parse_expression('initial_url')
response_meta = cst.parse_expression('response.meta.get("initial_url")')

with open(f"{PROJECT_REFACTOR_PATH}/templates/start_req_base.py") as sre:
    base_req_template = cst.parse_module(sre.read())
