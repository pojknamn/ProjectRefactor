import libcst as cst
from libcst import matchers as m
from conf import logger
from templates import response_meta, start_url_meta, base_req_template


class MetaInitUrlTransformer(cst.CSTTransformer):

    def __init__(self, response=False):
        super(MetaInitUrlTransformer, self).__init__()
        self.response = response

    @staticmethod
    def node_to_code(node: cst.CSTNode, return_code=False):
        """Convert any CST Node to Code."""
        mod = cst.parse_module("")
        wrapped = mod.with_changes(body=[node])
        print(wrapped.code)
        if return_code:
            return wrapped.code

    def leave_Arg(
            self, original_node: cst.Arg, updated_node: cst.Arg
    ) -> [cst.Arg | cst.FlattenSentinel[cst.Arg] | cst.RemovalSentinel]:
        try:
            if m.matches(updated_node.keyword, m.Name(value="meta")):

                elements = getattr(updated_node.value, 'elements', None)
                if elements is None:
                    raise ValueError
                init_val = response_meta if self.response else start_url_meta
                if elements:
                    has_init_url = [elem for elem in elements if (
                        not isinstance(elem.value, cst.Dict)) and elem.key.value == "'initial_url'"]
                    if not has_init_url:
                        new_elements = (
                            *elements[:-1],
                            elements[-1].with_changes(comma=cst.Comma()),
                            cst.DictElement(
                                key=cst.SimpleString(value="'initial_url'"), value=init_val
                            ),
                        )
                    else:
                        return updated_node
                else:
                    new_elements = (cst.DictElement(
                        key=cst.SimpleString(value="'initial_url'"), value=init_val
                    ),
                    )
                new_dict = cst.Dict(elements=new_elements)
                updated_node = updated_node.with_deep_changes(updated_node, value=new_dict)
        except ValueError:
            raise ValueError(f'error : {self.node_to_code(updated_node, return_code=True)}')
        return updated_node


class YieldTransformer(cst.CSTTransformer):
    def __init__(self, response=False):
        super(YieldTransformer, self).__init__()
        self.response = response

    def leave_Yield(
            self, original_node: cst.Yield, updated_node: cst.Yield
    ) -> cst.Yield:
        if m.matches(updated_node, m.Yield(value=m.Call(m.Name(m.MatchRegex(r'\w*Request'))))):
            updated_node = update_yields(updated_node, response=self.response)
        return updated_node

    def leave_Return(
            self, original_node: cst.Return, updated_node: cst.Return
    ):
        if m.matches(updated_node, m.Return(value=m.Call(m.Name(m.MatchRegex(r'\w*Request'))))):
            updated_node = update_yields(updated_node, response=self.response)
        return updated_node


def update_yields(node: cst.Yield | cst.Return, response=False) -> cst.Yield:
    yield_args = node.value.args
    meta_in_args = [meta for meta in yield_args if meta.keyword and meta.keyword.value == 'meta']
    init_val = response_meta if response else start_url_meta
    if not meta_in_args:
        new_args = [*yield_args,
                    cst.Arg(keyword=cst.Name('meta'), value=cst.Dict(elements=[cst.DictElement(
                        key=cst.SimpleString(value="'initial_url'"), value=init_val
                    ), ]))]
        old_call = node.value
        new_call = old_call.with_changes(args=new_args)
        updated = node.with_changes(value=new_call)
    else:
        updated = node.visit(MetaInitUrlTransformer(response=response))
    return updated


def update_for_loop(element):
    old_for_body = element.body.body
    try:
        initial_target = element.target.value
    except AttributeError:
        raise ValueError('Something went wrong while updating start_requests method')
    new_line = cst.SimpleStatementLine(
        body=[
            cst.Assign(
                targets=[cst.AssignTarget(target=cst.Name('initial_url'))],
                value=cst.Name(initial_target),
            )
        ]
    )

    new_for_body = cst.IndentedBlock(body=[new_line, *old_for_body])
    element = element.with_changes(body=new_for_body)
    return element


class ForLoopTransformer(cst.CSTTransformer):
    def __init__(self, for_loop=None):
        super(ForLoopTransformer, self).__init__()
        self.for_loop = for_loop

    def leave_For(
            self, original_node: cst.For, updated_node: cst.For
    ) -> [cst.BaseStatement | cst.FlattenSentinel[cst.BaseStatement] | cst.RemovalSentinel]:
        node = update_for_loop(updated_node)
        self.for_loop.append('For is here')
        return node


class ClassTransformer(cst.CSTTransformer):
    """Проходит по классам и добавляет старт реквестс если их нет."""

    @staticmethod
    def update_start_req(node: cst.BaseStatement) -> cst.BaseStatement:
        for_in_start_req = []
        func_body = node.visit(ForLoopTransformer(for_in_start_req))
        if not for_in_start_req:
            raise ValueError('There is no for cycle')
        return func_body

    @staticmethod
    def start_req_match(node: cst.CSTNode) -> bool:
        if m.matches(node, m.FunctionDef(name=m.Name('start_requests'))):
            return True

    @staticmethod
    def init_match(node: cst.CSTNode) -> bool:
        if m.matches(node, m.FunctionDef(name=m.Name('__init__'))):
            return True

    def leave_ClassDef(
            self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> [cst.BaseStatement | cst.FlattenSentinel[cst.BaseStatement], cst.RemovalSentinel]:
        original_class_name = original_node.name.value
        class_name = original_class_name.lower()
        have_start_req = False
        init_in_methods = False
        if "spider" in class_name:
            class_methods = updated_node.body.body
            have_start_req, init_in_methods = \
                self.find_init_and_start_req(
                    class_methods,
                    have_start_req,
                    init_in_methods,
                )
            new_methods = []
            try:
                if have_start_req:
                    for method in class_methods:
                        if self.start_req_match(method):
                            method = self.update_start_req(method)
                        response = self._get_function_parameters(method)
                        method = method.visit(YieldTransformer(response=response))
                        new_methods.append(method)
                else:
                    if init_in_methods:
                        init_index = self._get_init_index(class_methods)
                        new_body = cst.IndentedBlock([
                            *class_methods[:init_index],
                            base_req_template.body[0],
                            *class_methods[init_index:]
                        ])
                        updated_node = updated_node.with_changes(body=new_body)
                    class_methods = updated_node.body.body
                    for method in class_methods:
                        response = self._get_function_parameters(method)
                        method = method.visit(YieldTransformer(response=response))
                        new_methods.append(method)
            except ValueError as err:
                logger.error(
                    f"{original_class_name} - {type(err).__name__} {err.args[0]}\n")
                return original_node

            methods_indent = cst.IndentedBlock(body=new_methods)
            updated_node = updated_node.with_changes(body=methods_indent)

        return updated_node

    def find_init_and_start_req(self, class_methods, have_start_req, init_in_methods):
        for method in class_methods:
            if self.start_req_match(method):
                have_start_req = True
            if self.init_match(method):
                init_in_methods = True
        return have_start_req, init_in_methods

    @staticmethod
    def _get_function_parameters(method):
        if isinstance(method, cst.FunctionDef):
            params = [param.name.value for param in method.params.params]
        else:
            params = []
        return True if 'response' in params else False

    @staticmethod
    def _get_init_index(class_methods):
        init_index = -1
        for init_index, elem in enumerate(class_methods):
            if m.matches(elem, m.FunctionDef(name=m.Name('__init__'))):
                break
        init_index += 1
        return init_index
