# preprocessor.py

import os
import re


_identifier = re.compile(
    r'[A-Za-z_]\w*'
)


# =========================================================
# Evaluate preprocessor expressions
# =========================================================

def eval_pp_expr(expr, defines):

    expr = re.sub(
        r'\\\s*',
        ' ',
        expr
    )

    expr = re.sub(
        r'defined\s*\(\s*([A-Za-z_]\w*)\s*\)',
        lambda m:
            "1"
            if m.group(1) in defines
            else "0",
        expr
    )

    expr = re.sub(
        r'defined\s+([A-Za-z_]\w*)',
        lambda m:
            "1"
            if m.group(1) in defines
            else "0",
        expr
    )

    # ---------------------------------------------------------
    # Function-like macros
    # ---------------------------------------------------------

    expr = re.sub(
        r'\b[A-Za-z_]\w*\s*\([^()]*\)',
        lambda m:
            str(
                defines.get(
                    re.match(
                        r'[A-Za-z_]\w*',
                        m.group(0)
                    ).group(0),
                    0
                )
            )
            if isinstance(
                defines.get(
                    re.match(
                        r'[A-Za-z_]\w*',
                        m.group(0)
                    ).group(0)
                ),
                int
            )
            else "0",
        expr
    )

    # ---------------------------------------------------------
    # Replace identifiers
    # ---------------------------------------------------------

    def replace_identifier(match):

        name = match.group(0)

        if name in (
            "and",
            "or",
            "not"
        ):
            return name

        value = defines.get(name)

        if isinstance(value, int):
            return str(value)

        return "0"

    expr = _identifier.sub(
        replace_identifier,
        expr
    )

    expr = expr.replace(
        "&&",
        " and "
    )

    expr = expr.replace(
        "||",
        " or "
    )

    expr = re.sub(
        r'!(?!=)',
        " not ",
        expr
    )

    expr = expr.replace(
        "\\",
        " "
    )

    try:

        return bool(
            eval(
                expr,
                {
                    "__builtins__": {}
                },
                {}
            )
        )

    except Exception:

        return False


# =========================================================
# Remove comments safely
# =========================================================

def remove_comments(text):

    result = []

    i = 0
    length = len(text)

    state = "normal"

    while i < length:

        ch = text[i]

        if state == "normal":

            if (
                ch == "/"
                and i + 1 < length
                and text[i + 1] == "/"
            ):

                result.append(" ")

                i += 2

                while (
                    i < length
                    and text[i] != "\n"
                ):

                    i += 1

                continue

            if (
                ch == "/"
                and i + 1 < length
                and text[i + 1] == "*"
            ):

                result.append(" ")

                i += 2

                while i + 1 < length:

                    if (
                        text[i] == "*"
                        and text[i + 1] == "/"
                    ):

                        i += 2
                        break

                    if text[i] == "\n":
                        result.append("\n")

                    i += 1

                continue

            if ch == '"':

                state = "string"

                result.append(ch)

                i += 1

                continue

            if ch == "'":

                state = "char"

                result.append(ch)

                i += 1

                continue

            result.append(ch)

            i += 1

            continue

        if state == "string":

            result.append(ch)

            if ch == "\\":

                if i + 1 < length:

                    result.append(
                        text[i + 1]
                    )

                    i += 2

                    continue

            if ch == '"':

                state = "normal"

            i += 1

            continue

        if state == "char":

            result.append(ch)

            if ch == "\\":

                if i + 1 < length:

                    result.append(
                        text[i + 1]
                    )

                    i += 2

                    continue

            if ch == "'":

                state = "normal"

            i += 1

            continue

    return "".join(result)


# =========================================================
# Split C++ parameter list
# =========================================================

def split_parameters(parameters):

    result = []

    current = []

    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    angle_depth = 0

    i = 0

    while i < len(parameters):

        ch = parameters[i]

        if ch == "(":

            paren_depth += 1
            current.append(ch)
            i += 1
            continue

        if ch == ")":

            if paren_depth > 0:
                paren_depth -= 1

            current.append(ch)
            i += 1
            continue

        if ch == "[":

            bracket_depth += 1
            current.append(ch)
            i += 1
            continue

        if ch == "]":

            if bracket_depth > 0:
                bracket_depth -= 1

            current.append(ch)
            i += 1
            continue

        if ch == "{":

            brace_depth += 1
            current.append(ch)
            i += 1
            continue

        if ch == "}":

            if brace_depth > 0:
                brace_depth -= 1

            current.append(ch)
            i += 1
            continue

        if ch == "<":

            angle_depth += 1
            current.append(ch)
            i += 1
            continue

        if ch == ">":

            if angle_depth > 0:
                angle_depth -= 1

            current.append(ch)
            i += 1
            continue

        if (
            ch == ","
            and paren_depth == 0
            and bracket_depth == 0
            and brace_depth == 0
            and angle_depth == 0
        ):

            param = "".join(
                current
            ).strip()

            if param:
                result.append(param)

            current = []

            i += 1

            continue

        current.append(ch)

        i += 1

    param = "".join(
        current
    ).strip()

    if param:
        result.append(param)

    return result


# =========================================================
# Remove default argument
# =========================================================

def remove_default_argument(param):

    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    angle_depth = 0

    i = 0

    while i < len(param):

        ch = param[i]

        if ch == "(":
            paren_depth += 1

        elif ch == ")":

            if paren_depth > 0:
                paren_depth -= 1

        elif ch == "[":
            bracket_depth += 1

        elif ch == "]":

            if bracket_depth > 0:
                bracket_depth -= 1

        elif ch == "{":
            brace_depth += 1

        elif ch == "}":

            if brace_depth > 0:
                brace_depth -= 1

        elif ch == "<":
            angle_depth += 1

        elif ch == ">":

            if angle_depth > 0:
                angle_depth -= 1

        elif (
            ch == "="
            and paren_depth == 0
            and bracket_depth == 0
            and brace_depth == 0
            and angle_depth == 0
        ):

            return param[:i].strip()

        i += 1

    return param.strip()


# =========================================================
# Remove parameter name
# =========================================================

def remove_parameter_name(param):

    param = remove_default_argument(param)

    param = param.strip()

    if not param:
        return ""

    if param == "...":
        return "..."

    # -----------------------------------------------------
    # Function pointer
    # -----------------------------------------------------

    param = re.sub(
        r'\(\s*\*\s*[A-Za-z_]\w*\s*\)',
        '(*)',
        param
    )

    param = re.sub(
        r'\(\s*&\s*[A-Za-z_]\w*\s*\)',
        '(&)',
        param
    )

    # -----------------------------------------------------
    # Array parameter
    # -----------------------------------------------------

    m = re.match(
        r'^(.*?)(?:\s+)([A-Za-z_]\w*)'
        r'\s*(\[[^\]]*\])$',
        param
    )

    if m:

        param = (
            m.group(1)
            + " "
            + m.group(3)
        )

    else:

        m = re.match(
            r'^(.*\S)\s+([A-Za-z_]\w*)$',
            param
        )

        if m:

            before = m.group(1)
            name = m.group(2)

            keywords = {
                "const",
                "volatile",
                "static",
                "mutable",
                "unsigned",
                "signed",
                "short",
                "long",
                "int",
                "char",
                "float",
                "double",
                "bool",
                "void",
                "auto",
                "decltype",
                "typename",
                "class",
                "struct",
                "enum"
            }

            if name not in keywords:
                param = before

    param = re.sub(
        r'\s*\*\s*',
        ' *',
        param
    )

    param = re.sub(
        r'\s*&\s*',
        ' &',
        param
    )

    param = re.sub(
        r'\s+',
        ' ',
        param
    )

    return param.strip()


# =========================================================
# Normalize prototype
# =========================================================

def normalize_prototype(prototype):

    prototype = " ".join(
        prototype.split()
    )

    prototype = prototype.strip()

    if not prototype.endswith(";"):
        return prototype

    start = -1
    depth = 0

    for i, ch in enumerate(prototype):

        if ch == "(":

            if depth == 0:

                start = i
                break

        elif ch == "<":

            depth += 1

        elif ch == ">":

            if depth > 0:
                depth -= 1

    if start < 0:
        return prototype

    depth = 0
    end = -1

    for i in range(
        start,
        len(prototype)
    ):

        ch = prototype[i]

        if ch == "(":
            depth += 1

        elif ch == ")":

            depth -= 1

            if depth == 0:

                end = i
                break

    if end < 0:
        return prototype

    prefix = prototype[
        :start + 1
    ]

    args = prototype[
        start + 1:end
    ]

    suffix = prototype[
        end:
    ]

    args = args.strip()

    if args == "void":

        return (
            prefix
            + "void"
            + suffix
        )

    new_args = []

    for arg in split_parameters(args):

        arg = remove_parameter_name(arg)

        if arg:
            new_args.append(arg)

    result = (
        prefix
        + ", ".join(new_args)
        + suffix
    )

    result = re.sub(
        r'\s+',
        ' ',
        result
    )

    result = re.sub(
        r'\s+\)',
        ')',
        result
    )

    result = re.sub(
        r'\(\s+',
        '(',
        result
    )

    result = re.sub(
        r'\s*::\s*',
        '::',
        result
    )

    result = result.strip()

    return result


# =========================================================
# Pure virtual declaration
# =========================================================

def is_pure_virtual(statement):

    body = statement.strip()

    if body.endswith(";"):
        body = body[:-1].strip()

    # Examples:
    #
    #   virtual void Foo() = 0
    #   virtual bool DOS_File::Read(...) = 0
    #
    return bool(
        re.search(
            r'=\s*0\s*$',
            body
        )
    )


# =========================================================
# Extract class/struct name from declaration
# =========================================================

def extract_class_name(statement):

    statement = statement.strip()

    m = re.match(
        r'^(?:class|struct)\s+'
        r'([A-Za-z_]\w*(?:::\w+)*)'
        r'(?:\s*:[^{]+)?\s*\{',
        statement
    )

    if m:
        return m.group(1)

    return None


# =========================================================
# Determine whether a statement is a C/C++ prototype
# =========================================================

def is_prototype(statement):

    statement = statement.strip()

    if not statement.endswith(";"):
        return False

    if statement.startswith("#"):
        return False

    body = statement[:-1].strip()

    if not body:
        return False

    if re.match(
        r'^(?:'
        r'if|else|while|for|switch|do|'
        r'case|default|break|continue|'
        r'goto|return|catch|throw'
        r')\b',
        body
    ):
        return False

    if re.match(
        r'^(?:typedef|using)\b',
        body
    ):
        return False

    if "(" not in body:
        return False

    if ")" not in body:
        return False

    start = body.find("(")

    if start <= 0:
        return False

    prefix = body[:start].strip()

    if not prefix:
        return False

    # -----------------------------------------------------
    # Reject assignments / initializers.
    # -----------------------------------------------------

    assignment = re.search(
        r'(?<![=!<>])=(?!=)',
        prefix
    )

    if assignment:

        if not re.search(
            r'\boperator\s*=',
            prefix
        ):
            return False

    if re.search(
        r'\b(?:return|throw)\b',
        prefix
    ):
        return False

    prefix_without_qualifiers = re.sub(
        r'\b(?:'
        r'static|'
        r'inline|'
        r'virtual|'
        r'constexpr|'
        r'consteval|'
        r'constinit|'
        r'friend|'
        r'explicit|'
        r'extern|'
        r'mutable|'
        r'register'
        r')\b\s*',
        '',
        prefix
    ).strip()

    if not prefix_without_qualifiers:
        return False

    if re.fullmatch(
        r'[A-Za-z_]\w*',
        prefix_without_qualifiers
    ):
        return False

    if "." in prefix_without_qualifiers:
        return False

    if "->" in prefix_without_qualifiers:
        return False

    if re.search(
        r'\(\s*[*&]\s*[A-Za-z_]\w*\s*\)',
        body
    ):
        return False

    if "{" in body or "}" in body:
        return False

    function_name_pattern = (
        r'(?:'
        r'[A-Za-z_]\w*'
        r'|~[A-Za-z_]\w*'
        r'|operator\s*'
        r'(?:'
        r'new|delete|'
        r'new\[\]|delete\[\]|'
        r'<<=|>>=|<<|>>|'
        r'==|!=|<=|>=|'
        r'\+\+|--|&&|\|\||'
        r'->\*|->|'
        r'\+|-|\*|/|%|'
        r'&|\||\^|'
        r'~|!|=|<|>|'
        r'\(\)|\[\]'
        r'|[A-Za-z_]\w*'
        r')'
        r')'
    )

    qualified_name_pattern = (
        r'(?:'
        r'[A-Za-z_]\w*::'
        r')*'
        + function_name_pattern
    )

    if not re.search(
        qualified_name_pattern + r'\s*$',
        prefix_without_qualifiers
    ):
        return False

    name_match = re.search(
        r'(?:'
        r'[A-Za-z_]\w*'
        r'|~[A-Za-z_]\w*'
        r'|operator\s*'
        r'(?:new|delete|new\[\]|delete\[\]|'
        r'<<=|>>=|<<|>>|==|!=|<=|>=|'
        r'\+\+|--|&&|\|\||->\*|->|'
        r'\+|-|\*|/|%|&|\||\^|~|!|=|<|>|'
        r'\(\)|\[\]|[A-Za-z_]\w*)'
        r')$',
        prefix_without_qualifiers
    )

    if "::" in prefix_without_qualifiers:
        return True

    if re.search(
        r'\boperator\b',
        prefix_without_qualifiers
    ):
        return True

    if not name_match:
        return False

    function_name = name_match.group(0)

    return_type = prefix_without_qualifiers[
        :name_match.start()
    ].strip()

    if not return_type:
        return False

    if re.search(
        r'[=+\-/!|^]',
        return_type
    ):
        return False

    if "[" in return_type or "]" in return_type:
        return False

    if "." in return_type:
        return False

    return_type_pattern = re.compile(
        r'^(?:'
        r'(?:const\s+|volatile\s+|'
        r'unsigned\s+|signed\s+|'
        r'long\s+|short\s+)*'
        r'[A-Za-z_]\w*'
        r'(?:\s*::\s*[A-Za-z_]\w*)*'
        r'(?:\s*<[^;{}()]*>)?'
        r'(?:\s*[\*&]+)?'
        r')$'
    )

    if not return_type_pattern.fullmatch(
        return_type
    ):
        return False

    return True


# =========================================================
# Qualify prototype with current class
# =========================================================

def qualify_prototype(
    prototype,
    class_stack
):

    if not class_stack:
        return prototype

    prototype = prototype.strip()

    # -----------------------------------------------------
    # Already qualified
    # -----------------------------------------------------

    if "::" in prototype.split("(", 1)[0]:
        return prototype

    # -----------------------------------------------------
    # Do not qualify operators blindly.
    #
    # They are handled separately by compare.py.
    # -----------------------------------------------------

    if re.search(
        r'\boperator\b',
        prototype
    ):
        return prototype

    # -----------------------------------------------------
    # Find function opening parenthesis
    # -----------------------------------------------------

    pos = prototype.find("(")

    if pos < 0:
        return prototype

    prefix = prototype[:pos]

    m = re.search(
        r'([A-Za-z_]\w*)\s*$',
        prefix
    )

    if not m:
        return prototype

    name = m.group(1)

    scope = "::".join(
        class_stack
    )

    qualified_prefix = (
        prefix[:m.start()]
        + scope
        + "::"
        + name
    )

    return (
        qualified_prefix
        + prototype[pos:]
    )


# =========================================================
# Process one preprocessor conditional
# =========================================================

def process_condition(
    line,
    stack,
    defines
):

    m = re.match(
        r'#\s*ifdef\s+(\w+)',
        line
    )

    if m:

        cond = (
            m.group(1)
            in defines
        )

        stack.append(
            {
                "parent":
                    stack[-1]["active"],

                "active":
                    stack[-1]["active"]
                    and cond,

                "taken":
                    cond
            }
        )

        return True

    m = re.match(
        r'#\s*ifndef\s+(\w+)',
        line
    )

    if m:

        cond = (
            m.group(1)
            not in defines
        )

        stack.append(
            {
                "parent":
                    stack[-1]["active"],

                "active":
                    stack[-1]["active"]
                    and cond,

                "taken":
                    cond
            }
        )

        return True

    m = re.match(
        r'#\s*if\s+(.*)',
        line
    )

    if m:

        cond = eval_pp_expr(
            m.group(1),
            defines
        )

        stack.append(
            {
                "parent":
                    stack[-1]["active"],

                "active":
                    stack[-1]["active"]
                    and cond,

                "taken":
                    cond
            }
        )

        return True

    m = re.match(
        r'#\s*elif\s+(.*)',
        line
    )

    if m:

        level = stack[-1]

        if level["taken"]:

            level["active"] = False

        else:

            cond = eval_pp_expr(
                m.group(1),
                defines
            )

            level["active"] = (
                level["parent"]
                and cond
            )

            if cond:
                level["taken"] = True

        return True

    if re.match(
        r'#\s*else\b',
        line
    ):

        level = stack[-1]

        level["active"] = (
            level["parent"]
            and not level["taken"]
        )

        level["taken"] = True

        return True

    if re.match(
        r'#\s*endif\b',
        line
    ):

        if len(stack) > 1:
            stack.pop()

        return True

    return False


# =========================================================
# Parse preprocessor / C++ header
# =========================================================

def parse_preprocessor(
        file_path,
        defines=None,
        prototypes=None,
        visited=None,
        include_paths=None,
        extract_prototypes=True):

    if defines is None:
        defines = {}

    if prototypes is None:
        prototypes = []

    if visited is None:
        visited = set()

    if include_paths is None:
        include_paths = []

    file_path = os.path.abspath(
        file_path
    )

    if file_path in visited:

        return (
            defines,
            prototypes
        )

    visited.add(
        file_path
    )

    current_dir = os.path.dirname(
        file_path
    )

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            text = f.read()

    except FileNotFoundError:

        return (
            defines,
            prototypes
        )

    text = remove_comments(
        text
    )

    stack = [
        {
            "parent": True,
            "active": True,
            "taken": False
        }
    ]

    statement = ""

    # =====================================================
    # NEW:
    #
    # Track class / struct nesting.
    #
    # Example:
    #
    # class A {
    #     class B {
    #         void foo();
    #     };
    # };
    #
    # class_stack becomes:
    #
    # ["A"]
    # ["A", "B"]
    # =====================================================

    class_stack = []

    # Number of braces belonging to classes.
    class_brace_depth = []

    brace_depth = 0

    # -----------------------------------------------------
    # Process lines
    # -----------------------------------------------------

    for raw in text.splitlines():

        line = raw.strip()

        if not line:
            continue

        # =================================================
        # Preprocessor conditionals
        # =================================================

        if process_condition(
            line,
            stack,
            defines
        ):
            continue

        if not stack[-1]["active"]:
            continue

        # =================================================
        # Include
        # =================================================

        m = re.match(
            r'#\s*include\s*[<"]'
            r'([^>"]+)'
            r'[>"]',
            line
        )

        if m:

            filename = m.group(1)

            paths = [
                current_dir
            ]

            paths.extend(
                include_paths
            )

            for path in paths:

                include_file = os.path.abspath(
                    os.path.join(
                        path,
                        filename
                    )
                )

                if os.path.isfile(
                    include_file
                ):

                    parse_preprocessor(
                        include_file,
                        defines=defines,
                        prototypes=prototypes,
                        visited=visited,
                        include_paths=include_paths,
                        extract_prototypes=extract_prototypes
                    )

                    break

            continue

        # =================================================
        # Define
        # =================================================

        m = re.match(
            r'#\s*define\s+'
            r'(\w+)'
            r'(?:\s+(.*))?$',
            line
        )

        if m:

            name = m.group(1)

            value = m.group(2)

            if value is None:

                defines[name] = 1

            else:

                value = value.strip()

                try:

                    defines[name] = int(
                        value,
                        0
                    )

                except Exception:

                    defines[name] = value

            continue

        # =================================================
        # Undef
        # =================================================

        m = re.match(
            r'#\s*undef\s+(\w+)',
            line
        )

        if m:

            defines.pop(
                m.group(1),
                None
            )

            continue

        if line.startswith("#"):
            continue

        # =================================================
        # Detect class / struct declaration
        # =================================================

        class_match = re.match(
            r'^(?:class|struct)\s+'
            r'([A-Za-z_]\w*(?:::\w+)*)'
            r'(?:\s*:[^{]+)?\s*\{',
            line
        )

        if class_match:

            class_name = class_match.group(1)

            class_stack.append(
                class_name
            )

            # This line introduces one class brace.
            class_brace_depth.append(
                brace_depth
            )

        # =================================================
        # Prototype collection
        # =================================================

        if extract_prototypes:

            statement += " " + line

            if ";" in line:

                parts = statement.split(";")

                for part in parts[:-1]:

                    stmt = (
                        " ".join(
                            part.split()
                        )
                        + ";"
                    )

                    if is_prototype(stmt):

                        # ---------------------------------
                        # Pure virtual functions are
                        # declarations, but they do not
                        # require an implementation.
                        # ---------------------------------

                        if is_pure_virtual(stmt):

                            continue

                        normalized = normalize_prototype(
                            stmt
                        )

                        normalized = qualify_prototype(
                            normalized,
                            class_stack
                        )

                        if normalized not in prototypes:

                            prototypes.append(
                                normalized
                            )

                statement = parts[-1].strip()

        # =================================================
        # Update brace depth
        # =================================================

        opens = line.count("{")
        closes = line.count("}")

        brace_depth += opens
        brace_depth -= closes

        if brace_depth < 0:
            brace_depth = 0

        # =================================================
        # Leave class scope
        # =================================================

        while (
            class_stack
            and class_brace_depth
            and brace_depth <= class_brace_depth[-1]
        ):

            class_stack.pop()
            class_brace_depth.pop()

    return (
        defines,
        prototypes
    )