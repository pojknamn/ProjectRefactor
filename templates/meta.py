import libcst as cst
start_url_meta = cst.parse_expression('initial_url')
response_meta = cst.parse_expression('response.meta.get("initial_url")')

with open("templates/start_req_base.py") as sre:
    base_req_template = cst.parse_module(sre.read())
