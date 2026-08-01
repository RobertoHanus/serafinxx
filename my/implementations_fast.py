import os
import re


# =========================================================
# Precompiled regular expressions
# =========================================================

_RE_SPACE_CLOSE = re.compile(r'\s+\)')
_RE_OPEN_SPACE = re.compile(r'\(\s+')
_RE_COMMA_SPACE = re.compile(r'\s*,\s*')
_RE_SCOPE_SPACE = re.compile(r'\s*::\s*')
_RE_AMP_SPACE = re.compile(r'\s*&\s*')
_RE_STAR_SPACE = re.compile(r'\s+\*')

_RE_FUNCTION_PREFIX = re.compile(
    r'(?:[A-Za-z_~]\w*|operator\s*\S+|\))$'
)

_RE_ARRAY_PARAM = re.compile(
    r'^(.*?)(?:\s+)([A-Za-z_]\w*)\s*(\[[^\]]*\])$'
)

_RE_FINAL_IDENTIFIER = re.compile(
    r'^(.*\S)\s+([A-Za-z_]\w*)$'
)

_RE_FUNCTION_POINTER = re.compile(
    r'\(\s*\*\s*[A-Za-z_]\w*\s*\)'
)

_RE_FUNCTION_REFERENCE = re.compile(
    r'\(\s*&\s*[A-Za-z_]\w*\s*\)'
)

_RE_IDENTIFIER_END = re.compile(
    r'([A-Za-z_]\w*)$'
)

_RE_ASSIGNMENT = re.compile(
    r'(?<![=!<>])=(?!=)'
)

_RE_ASSIGNMENT_NAME = re.compile(
    r'\b[A-Za-z_]\w*\s*=\s*'
)

_RE_RETURN_THROW = re.compile(
    r'\b(?:return|throw|case)\b'
)

_RE_ARITHMETIC = re.compile(
    r'(?<!:)[+\-/%!|^](?!>)'
)

_RE_CONTROL = re.compile(
    r'^\s*(?:if|else|for|while|switch|catch|do)\b'
)

_RE_DECL_QUALIFIERS = re.compile(
    r'\b(?:virtual|static|inline|extern|constexpr|consteval|friend|'
    r'explicit|mutable|register|const|volatile)\b'
)

_RE_NESTED_CALL = re.compile(
    r'\([^()]*\)'
)

_RE_OPERATOR = re.compile(
    r'\boperator\b'
)

_RE_OPERATOR_SYMBOL = re.compile(
    r'((?:[A-Za-z_]\w*::)*operator\s*'
    r'(?:new|delete|new\[\]|delete\[\]|'
    r'<<=|>>=|<<|>>|==|!=|<=|>=|'
    r'\+\+|--|&&|\|\||->\*|->|'
    r'\+|-|\*|/|%|&|\||\^|'
    r'~|!|=|<|>|'
    r'\(\)|\[\]))$'
)

_RE_OPERATOR_CONVERSION = re.compile(
    r'((?:[A-Za-z_]\w*::)*operator\s+'
    r'(?:const\s+|volatile\s+|unsigned\s+|signed\s+|'
    r'long\s+|short\s+)*'
    r'[A-Za-z_]\w*'
    r'(?:\s*::\s*[A-Za-z_]\w*)*'
    r'(?:\s*<[^(){};]*>)?'
    r'(?:\s*[\*&]+)?)$'
)

_RE_DESTRUCTOR_NAME = re.compile(
    r'((?:[A-Za-z_]\w*::)*~[A-Za-z_]\w*)$'
)

_RE_NORMAL_FUNCTION_NAME = re.compile(
    r'((?:[A-Za-z_]\w*::)*[A-Za-z_]\w*)$'
)

_RE_WHILE_AFTER_BRACE = re.compile(
    r'^\}\s*while\s*\([^)]*\)\s*'
)

_RE_UPPERCASE_MACRO = re.compile(
    r'^[A-Z_][A-Z0-9_]*\s*\([^)]*\)\s*$'
)

_RE_ASSIGNMENT_OPERATOR = re.compile(
    r'\boperator\s*='
)

_RE_FUNCTION_CALL_NAME = re.compile(
    r'[A-Za-z_]\w*\s*$'
)


# =========================================================
# Normalize spaces
# =========================================================

def clean_spaces(text):

    text = " ".join(text.split())

    text = _RE_SPACE_CLOSE.sub(")", text)
    text = _RE_OPEN_SPACE.sub("(", text)
    text = _RE_COMMA_SPACE.sub(", ", text)
    text = _RE_SCOPE_SPACE.sub("::", text)
    text = _RE_AMP_SPACE.sub(" &", text)
    text = _RE_STAR_SPACE.sub(" *", text)

    return text.strip()


# =========================================================
# Remove comments
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

                while i < length and text[i] != "\n":
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

                    result.append(text[i + 1])
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

                    result.append(text[i + 1])
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
    length = len(parameters)

    while i < length:

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

            next_char = ""

            if i + 1 < length:
                next_char = parameters[i + 1]

            if (
                next_char.isalnum()
                or next_char in "_>:*&"
            ):
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

            param = "".join(current).strip()

            if param:
                result.append(param)

            current = []

            i += 1
            continue

        current.append(ch)
        i += 1

    param = "".join(current).strip()

    if param:
        result.append(param)

    return result


# =========================================================
# Remove default parameter value
# =========================================================

def remove_default_value(param):

    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    angle_depth = 0

    i = 0
    length = len(param)

    while i < length:

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
# Remove parameter variable name
# =========================================================

def remove_parameter_name(param):

    param = remove_default_value(param).strip()

    if not param:
        return ""

    if param == "...":
        return "..."

    # Function pointer

    param = _RE_FUNCTION_POINTER.sub(
        "(*)",
        param
    )

    # Function reference

    param = _RE_FUNCTION_REFERENCE.sub(
        "(&)",
        param
    )

    # Array parameter

    m = _RE_ARRAY_PARAM.match(param)

    if m:

        param = (
            m.group(1)
            + " "
            + m.group(3)
        )

    else:

        m = _RE_FINAL_IDENTIFIER.match(param)

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
        r"\s*\*\s*",
        " *",
        param
    )

    param = re.sub(
        r"\s*&\s*",
        " &",
        param
    )

    return clean_spaces(param)


# =========================================================
# Remove parameter names
# =========================================================

def remove_parameter_names(parameters):

    parameters = parameters.strip()

    if parameters == "void":
        return "void"

    if not parameters:
        return ""

    result = []

    for param in split_parameters(parameters):

        param = remove_parameter_name(param)

        if param:
            result.append(param)

    return ", ".join(result)


# =========================================================
# Find matching parenthesis
# =========================================================

def find_matching_paren(text, opening):

    depth = 0

    i = opening
    length = len(text)

    while i < length:

        ch = text[i]

        if ch == "(":

            depth += 1

        elif ch == ")":

            depth -= 1

            if depth == 0:
                return i

        i += 1

    return -1


# =========================================================
# Extract function parameter section
# =========================================================

def find_function_parameter_range(declaration):

    candidates = []

    angle_depth = 0

    i = 0
    length = len(declaration)

    while i < length:

        ch = declaration[i]

        if ch == "<":

            angle_depth += 1

        elif ch == ">":

            if angle_depth > 0:
                angle_depth -= 1

        elif ch == "(":

            if angle_depth == 0:
                candidates.append(i)

        i += 1

    for start in reversed(candidates):

        end = find_matching_paren(
            declaration,
            start
        )

        if end < 0:
            continue

        prefix = declaration[:start].strip()

        if not prefix:
            continue

        # -------------------------------------------------
        # Normal function
        # -------------------------------------------------

        if _RE_FUNCTION_PREFIX.search(prefix):
            return start, end

        # -------------------------------------------------
        # Conversion operator
        #
        # Example:
        #
        # Value::operator bool()
        # Value::operator Hex()
        # -------------------------------------------------

        if _RE_OPERATOR.search(prefix):
            return start, end

    return -1, -1


# =========================================================
# Normalize function declaration
# =========================================================

def normalize_function(declaration):

    declaration = clean_spaces(declaration)

    declaration = declaration.rstrip()

    if declaration.endswith("{"):
        declaration = declaration[:-1].strip()

    declaration = declaration.rstrip(";").strip()

    if not declaration:
        return None

    start, end = find_function_parameter_range(
        declaration
    )

    if start < 0 or end < 0:
        return None

    before = declaration[:start].strip()

    parameters = declaration[
        start + 1:end
    ].strip()

    after = declaration[
        end + 1:
    ].strip()

    suffix = ""

    if after:
        suffix = " " + after

    parameters = remove_parameter_names(
        parameters
    )

    result = (
        before
        + "("
        + parameters
        + ")"
        + suffix
        + ";"
    )

    return clean_spaces(result)


# =========================================================
# Extract function name
# =========================================================

def get_function_name(declaration):

    if not declaration:
        return None

    declaration = clean_spaces(declaration)

    start, end = find_function_parameter_range(
        declaration
    )

    if start < 0:
        return None

    prefix = declaration[:start].strip()

    if not prefix:
        return None

    # =====================================================
    # C++ operators
    # =====================================================

    if "operator" in prefix:

        # -------------------------------------------------
        # operator=, operator+, operator[], etc.
        # -------------------------------------------------

        m = _RE_OPERATOR_SYMBOL.search(prefix)

        if m:
            return m.group(1)

        # -------------------------------------------------
        # Conversion operators:
        #
        # Value::operator bool
        # Value::operator Hex
        # Value::operator int
        # Value::operator double
        # -------------------------------------------------

        m = _RE_OPERATOR_CONVERSION.search(prefix)

        if m:
            return clean_spaces(
                m.group(1)
            )

        # -------------------------------------------------
        # Fallback for unusual operator forms.
        # -------------------------------------------------

        m = re.search(
            r'((?:[A-Za-z_]\w*::)*operator\b.*)$',
            prefix
        )

        if m:

            name = clean_spaces(
                m.group(1)
            )

            return name

    # =====================================================
    # Destructor
    # =====================================================

    m = _RE_DESTRUCTOR_NAME.search(prefix)

    if m:
        return m.group(1)

    # =====================================================
    # Normal / qualified function
    # =====================================================

    m = _RE_NORMAL_FUNCTION_NAME.search(prefix)

    if m:
        return m.group(1)

    return None


# =========================================================
# Determine whether declaration is a function
# =========================================================

def looks_like_function(declaration):

    if not declaration:
        return False

    declaration = declaration.strip()

    if not declaration:
        return False

    if "(" not in declaration:
        return False

    if ")" not in declaration:
        return False

    declaration = clean_spaces(declaration)

    start, end = find_function_parameter_range(
        declaration
    )

    if start < 0 or end < 0:
        return False

    prefix = declaration[:start].strip()

    if not prefix:
        return False

    # =====================================================
    # Control statements
    # =====================================================

    if _RE_CONTROL.match(prefix):
        return False

    # =====================================================
    # Lambda
    # =====================================================

    if declaration.startswith("["):
        return False

    # =====================================================
    # C++ operator
    #
    # Operators are special and must NOT be subjected to
    # normal return-type validation.
    # =====================================================

    if _RE_OPERATOR.search(prefix):

        # Assignment operator

        if _RE_ASSIGNMENT_OPERATOR.search(prefix):
            return True

        # Conversion operator

        if _RE_OPERATOR_CONVERSION.search(prefix):
            return True

        # Symbol operator

        if _RE_OPERATOR_SYMBOL.search(prefix):
            return True

        return True

    # =====================================================
    # Assignment protection
    # =====================================================

    if _RE_ASSIGNMENT.search(prefix):
        return False

    # =====================================================
    # Expressions
    # =====================================================

    if _RE_RETURN_THROW.search(prefix):
        return False

    if _RE_ARITHMETIC.search(prefix):
        return False

    # =====================================================
    # Get function name
    # =====================================================

    name = get_function_name(
        declaration
    )

    if not name:
        return False

    # =====================================================
    # Destructor
    # =====================================================

    if "~" in name:
        return True

    # =====================================================
    # Scoped/member function
    # =====================================================

    if "::" in name:
        return True

    # =====================================================
    # Remove declaration qualifiers
    # =====================================================

    test_prefix = _RE_DECL_QUALIFIERS.sub(
        " ",
        prefix
    )

    test_prefix = clean_spaces(
        test_prefix
    )

    if not test_prefix:
        return False

    # =====================================================
    # Find final function identifier
    # =====================================================

    name_match = _RE_IDENTIFIER_END.search(
        test_prefix
    )

    if not name_match:
        return False

    before_name = test_prefix[
        :name_match.start()
    ].strip()

    if not before_name:
        return False

    # =====================================================
    # Return type
    # =====================================================

    return_type = before_name

    if not return_type:
        return False

    if re.search(
        r'[=+\-/!|^]',
        return_type
    ):
        return False

    if "." in return_type:
        return False

    if "[" in return_type or "]" in return_type:
        return False

    # =====================================================
    # Remove pointer/reference symbols
    # =====================================================

    type_for_validation = re.sub(
        r'[\*&]',
        " ",
        return_type
    )

    type_for_validation = clean_spaces(
        type_for_validation
    )

    if not type_for_validation:
        return False

    # =====================================================
    # Validate return type
    # =====================================================

    if not re.fullmatch(
        r'(?:(?:const\s+|volatile\s+|unsigned\s+|signed\s+|'
        r'long\s+|short\s+)*'
        r'[A-Za-z_]\w*'
        r'(?:\s*::\s*[A-Za-z_]\w*)*'
        r'(?:\s*<[^;{}()]*>)?)',
        type_for_validation
    ):
        return False

    # =====================================================
    # Nested function calls
    # =====================================================

    inner_prefix = declaration[:start]

    inner_prefix = _RE_FUNCTION_CALL_NAME.sub(
        "",
        inner_prefix
    ).strip()

    if _RE_NESTED_CALL.search(
        inner_prefix
    ):
        return False

    return True


# =========================================================
# Process preprocessor condition
# =========================================================

def process_condition(
    line,
    stack,
    defines,
    eval_pp_expr
):

    m = re.match(
        r'#\s*ifdef\s+(\w+)',
        line
    )

    if m:

        cond = m.group(1) in defines

        stack.append({
            "parent": stack[-1]["active"],
            "active": stack[-1]["active"] and cond,
            "taken": cond
        })

        return True

    m = re.match(
        r'#\s*ifndef\s+(\w+)',
        line
    )

    if m:

        cond = m.group(1) not in defines

        stack.append({
            "parent": stack[-1]["active"],
            "active": stack[-1]["active"] and cond,
            "taken": cond
        })

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

        stack.append({
            "parent": stack[-1]["active"],
            "active": stack[-1]["active"] and cond,
            "taken": cond
        })

        return True

    m = re.match(
        r'#\s*elif\s+(.*)',
        line
    )

    if m:

        if len(stack) <= 1:
            return True

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

        if len(stack) <= 1:
            return True

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
# Determine whether brace belongs to a function
# =========================================================

def find_function_brace(line):

    position = line.rfind("{")

    if position < 0:
        return -1

    prefix = line[:position].strip()

    if not prefix:
        return -1

    if "(" not in prefix:
        return -1

    if ")" not in prefix:
        return -1

    last_close = prefix.rfind(")")

    if last_close < 0:
        return -1

    after_close = prefix[
        last_close + 1:
    ].strip()

    # A declaration ending in ';' is not a definition.

    if after_close.endswith(";"):
        return -1

    if looks_like_function(prefix):
        return position

    return -1


# =========================================================
# Parse one C/C++ implementation file
# =========================================================

def parse_cpp_file(
    filename,
    relative_path,
    defines,
    functions,
    eval_pp_expr,
    verbose=False
):

    try:

        with open(
            filename,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            text = f.read()

    except (FileNotFoundError, OSError):

        return

    text = remove_comments(text)

    lines = text.splitlines()

    stack = [{
        "parent": True,
        "active": True,
        "taken": False
    }]

    function_depth = 0
    declaration = ""

    i = 0
    total_lines = len(lines)

    while i < total_lines:

        if verbose and i % 500 == 0:

            print(
                f"Parsing line {i + 1}/{total_lines} "
                f"in {relative_path}",
                flush=True
            )

        raw = lines[i]
        line = raw.strip()

        i += 1

        if not line:
            continue

        # -------------------------------------------------
        # Preprocessor
        # -------------------------------------------------

        if line.startswith("#"):

            process_condition(
                line,
                stack,
                defines,
                eval_pp_expr
            )

            continue

        # -------------------------------------------------
        # Inactive branch
        # -------------------------------------------------

        if not stack[-1]["active"]:
            continue

        # -------------------------------------------------
        # Inside function body
        # -------------------------------------------------

        if function_depth > 0:

            function_depth += line.count("{")
            function_depth -= line.count("}")

            if function_depth <= 0:

                function_depth = 0
                declaration = ""

            continue

        # -------------------------------------------------
        # Standalone closing brace
        # -------------------------------------------------

        if line == "}":

            declaration = ""
            continue

        # -------------------------------------------------
        # Closing brace
        # -------------------------------------------------

        if line.startswith("}"):

            line = _RE_WHILE_AFTER_BRACE.sub(
                "",
                line
            ).strip()

            declaration = ""

            if not line:
                continue

        # -------------------------------------------------
        # Uppercase macro
        # -------------------------------------------------

        if _RE_UPPERCASE_MACRO.match(line):

            declaration = ""
            continue

        # -------------------------------------------------
        # Accumulate declaration
        # -------------------------------------------------

        if declaration:
            declaration += " "

        declaration += line

        # -------------------------------------------------
        # No brace yet
        # -------------------------------------------------

        if "{" not in line:

            if ";" in line:
                declaration = ""

            continue

        # -------------------------------------------------
        # Function definition candidate
        # -------------------------------------------------

        brace_position = find_function_brace(
            declaration
        )

        if brace_position >= 0:

            header = declaration[
                :brace_position
            ].strip()

            if looks_like_function(header):

                normalized = normalize_function(
                    header
                )

                if normalized:

                    name = get_function_name(
                        normalized
                    )

                    if name:

                        functions.append({
                            "file": os.path.basename(
                                filename
                            ),
                            "path": relative_path,
                            "name": name,
                            "declaration": normalized
                        })

                # Enter function body.

                remaining = declaration[
                    brace_position:
                ]

                opens = remaining.count("{")
                closes = remaining.count("}")

                function_depth = opens - closes

                if function_depth < 0:
                    function_depth = 0

                declaration = ""

                continue

        # -------------------------------------------------
        # Not a function:
        # namespace/class/struct/etc.
        # -------------------------------------------------

        opens = declaration.count("{")
        closes = declaration.count("}")

        if opens or closes:

            declaration = ""

        elif ";" in line:

            declaration = ""


# =========================================================
# Parse directory
#
# IMPORTANT:
#
# Definitions can exist in:
#
#   .c
#   .cc
#   .cpp
#   .cxx
#   .C
#   .h
#   .hh
#   .hpp
#   .hxx
#
# DOSBox-X contains inline definitions in headers, e.g.
# writeString/readString in dosbox.h.
# =========================================================

def parse_implementations(
    directory,
    defines=None,
    eval_pp_expr=None,
    verbose=False
):

    if defines is None:
        defines = {}

    if eval_pp_expr is None:

        raise ValueError(
            "eval_pp_expr function is required"
        )

    project_root = os.path.abspath(
        directory
    )

    functions = []

    visited = set()

    implementation_extensions = {
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".C",
        ".h",
        ".hh",
        ".hpp",
        ".hxx"
    }

    for root, dirs, files in os.walk(
        directory
    ):

        for file in files:

            extension = os.path.splitext(
                file
            )[1]

            if extension not in implementation_extensions:
                continue

            filename = os.path.abspath(
                os.path.join(
                    root,
                    file
                )
            )

            if filename in visited:
                continue

            visited.add(filename)

            relative_path = os.path.relpath(
                filename,
                project_root
            )

            if verbose:

                print(
                    f"Parsing C/C++ file: {relative_path}",
                    flush=True
                )

            parse_cpp_file(
                filename,
                relative_path,
                defines,
                functions,
                eval_pp_expr,
                verbose=verbose
            )

    return functions


# =========================================================
# Optional helper
# =========================================================

def print_implementations(functions):

    for item in functions:

        print(
            f"{item['name']:35} "
            f"{item['file']:25} "
            f"{item['path']:45} "
            f"{item['declaration']}"
        )