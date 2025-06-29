import ast
import re

from typing import Optional
from dashcorn.command.default_inject_config import DEFAULT_INJECT_CONFIG

def insert_middleware_and_imports(
    source_code: str,
    import_statements: list[str],
    middleware_lines: list[str],
) -> str:
    """
    Find the first FastAPI() object and insert middleware lines after it.
    Also insert import lines if they don't already exist.
    """
    tree = ast.parse(source_code)
    lines = source_code.splitlines()
    new_lines = lines[:]

    # ===== 1. Insert middleware after FastAPI() object =====
    inserted = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            call = node.value
            if hasattr(call.func, "id") and call.func.id == "FastAPI":
                app_name = node.targets[0].id
                lineno = node.lineno - 1
                indent = len(lines[lineno]) - len(lines[lineno].lstrip())
                indent_str = " " * indent

                for offset, raw_line in enumerate(middleware_lines):
                    line = indent_str + raw_line.replace("<name_of_app>", app_name)
                    new_lines.insert(lineno + 1 + offset, line)
                inserted = True
                break

    if not inserted:
        raise ValueError("Could not find FastAPI instance in the source code.")

    # ===== 2. Insert missing import statements =====
    existing_source = "\n".join(lines)
    existing_imports = set(re.findall(r'^\s*(?:from|import)\s+[^\n]+', existing_source, re.MULTILINE))

    to_insert = []
    for imp in import_statements:
        if not any(imp in existing for existing in existing_imports):
            to_insert.append(imp)

    if to_insert:
        # Find the last import line
        last_import_idx = 0
        for idx, line in enumerate(lines):
            if re.match(r'^\s*(import|from)\s+', line):
                last_import_idx = idx
        for offset, imp in enumerate(to_insert):
            new_lines.insert(last_import_idx + 1 + offset, imp)

    return "\n".join(new_lines)

#--------------------------------------------------------------------------------------------------

import os

def inject_middlewares_to_source_file(
    file_path: str,
    config: dict = DEFAULT_INJECT_CONFIG,
    import_statements: Optional[list[str]] = None,
    middleware_lines: Optional[list[str]] = None,
    backup: bool = True
) -> None:
    """
    Read a Python source file, inject middleware & imports, then overwrite the file.
    If backup=True, a copy will be saved at <file_path>.bak.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Process the content
    updated_code = insert_middleware_and_imports(
        source_code=source_code,
        import_statements=import_statements or config.get("middleware", {}).get("imports", []),
        middleware_lines=middleware_lines or config.get("middleware", {}).get("lines", []),
    )

    # Create a backup if needed
    if backup:
        backup_path = file_path + ".bak"
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(source_code)

    # Overwrite with updated content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_code)

#--------------------------------------------------------------------------------------------------

import ast
import re

def insert_lifecycle_triggers_to_fastapi(
    source_code: str,
    import_statements: list[str],
    on_startup_triggers: list[str],
    on_shutdown_triggers: list[str],
) -> str:
    tree = ast.parse(source_code)

    class FastAPIRewriter(ast.NodeTransformer):
        def visit_Assign(self, node):
            if isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name) and func.id == "FastAPI":
                    keywords = {kw.arg: kw for kw in node.value.keywords}

                    def merge_list_arg(arg_name, new_items):
                        if arg_name in keywords:
                            kw_node = keywords[arg_name]
                            if isinstance(kw_node.value, ast.List):
                                existing_items = [elt.id for elt in kw_node.value.elts if isinstance(elt, ast.Name)]
                                combined = list(dict.fromkeys(existing_items + new_items))
                                kw_node.value.elts = [ast.Name(id=name, ctx=ast.Load()) for name in combined]
                        else:
                            new_kw = ast.keyword(
                                arg=arg_name,
                                value=ast.List(elts=[ast.Name(id=name, ctx=ast.Load()) for name in new_items], ctx=ast.Load())
                            )
                            node.value.keywords.append(new_kw)

                    merge_list_arg("on_startup", on_startup_triggers)
                    merge_list_arg("on_shutdown", on_shutdown_triggers)
            return node

    new_tree = FastAPIRewriter().visit(tree)
    ast.fix_missing_locations(new_tree)

    try:
        import astor
        updated_code = astor.to_source(new_tree)
    except ImportError:
        updated_code = ast.unparse(new_tree)

    existing_imports = set(re.findall(r'^\s*(?:from|import)\s+[^\n]+', source_code, re.MULTILINE))
    to_insert = [imp for imp in import_statements if not any(imp in exist for exist in existing_imports)]

    if to_insert:
        updated_lines = updated_code.splitlines()
        insert_idx = 0
        for idx, line in enumerate(updated_lines):
            if re.match(r'^\s*(import|from)\s+', line):
                insert_idx = idx
        for i, imp in enumerate(to_insert):
            updated_lines.insert(insert_idx + 1 + i, imp)
        updated_code = "\n".join(updated_lines)

    return updated_code

#--------------------------------------------------------------------------------------------------

import os

def inject_lifecycle_to_source_file(
    file_path: str,
    config: dict = DEFAULT_INJECT_CONFIG,
    import_statements: Optional[list[str]] = None,
    on_startup_triggers: Optional[list[str]] = None,
    on_shutdown_triggers: Optional[list[str]] = None,
    backup: bool = True
) -> None:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Tệp không tồn tại: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    updated_code = insert_lifecycle_triggers_to_fastapi(
        source_code=source_code,
        import_statements=import_statements or config.get("lifecycle", {}).get("imports", []),
        on_startup_triggers=on_startup_triggers or config.get("lifecycle", {}).get("on_startup", []),
        on_shutdown_triggers=on_shutdown_triggers or config.get("lifecycle", {}).get("on_shutdown", []),
    )

    if backup:
        with open(file_path + ".bak", "w", encoding="utf-8") as f:
            f.write(source_code)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_code)
