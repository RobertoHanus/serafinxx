import os
import re


# =========================================================
# Regular expressions
# =========================================================

_RE_SPACE_CLOSE = re.compile(r'\s+\)')
_RE_OPEN_SPACE = re.compile(r'\(\s+')
_RE_COMMA_SPACE = re.compile(r'\s*,\s*')
_RE_SCOPE_SPACE = re.compile(r'\s*::\s*')
_RE_AMP_SPACE = re.compile(r'\s*&\s*')
_RE_STAR_SPACE = re.compile(r'\s+\*')

_RE_ARRAY_PARAM = re.compile(
    r'^(.*?)(?:\s+)([A-Za-z_]\w*)\s*(\[[^\]]*\])$'
)

_RE_FINAL_IDENTIFIER = re.compile(
    r'^(.*\S)\s+([A-Za-z_]\w*)$'
)

_RE_FUNCTION_POINTER_NAME = re.compile(
    r'\(\s*[*&]\s*([A-Za-z_]\w*)\s*\)'
)

_RE_CONTROL = re.compile(
    r'^\s*(?:if|else|for|while|switch|catch|do)\b'
)

_RE_RETURN_THROW = re.compile(
    r'\b(?:return|throw|case)\b'
)

_RE_ASSIGNMENT = re.compile(
    r'(?<![=!<>])=(?!=)'
)

_RE_ASSIGNMENT_OPERATOR = re.compile(
    r'\boperator\s*='
)

_RE_UPPERCASE_MACRO = re.compile(
    r'^[A-Z_][A-Z0-9_]*\s*\([^)]*\)\s*$'
)

_RE_IDENTIFIER = re.compile(
    r'[A-Za-z_]\w*'
)

_RE_QUALIFIED_IDENTIFIER = re.compile(
    r'[A-Za-z_]\w*(?:\s*::\s*[A-Za-z_]\w*)*'
)

_RE_OPERATOR_TARGET = re.compile(
    r'(?:'
    r'new(?:\[\])?'
    r'|delete(?:\[\])?'
    r'|<<=?'
    r'|>>=?'
    r'|=='
    r'|!='
    r'|<='
    r'>='
    r'|\+\+'
    r'|--'
    r'|&&'
    r'|\|\|'
    r'|->\*'
    r'|->'
    r'|\+'
    r'-'
    r'\*'
    r'/'
    r'%'
    r'&'
    r'\|'
    r'\^'
    r'~'
    r'!'
    r'='
    r'<'
    r'>'
    r'|\(\)'
    r'|\[\]'
    r'|[A-Za-z_]\w*'
    r')'
)


# =========================================================
# Normalize spaces
# =========================================================

def clean_spaces(text):

    text = " ".join(text.split())

    text = _RE_SPACE_CLOSE.sub(
        ")",
        text
    )

    text = _RE_OPEN_SPACE.sub(
        "(",
        text
    )

    text = _RE_COMMA_SPACE.sub(
        ", ",
        text
    )

    text = _RE_SCOPE_SPACE.sub(
        "::",
        text
    )

    text = _RE_AMP_SPACE.sub(
        " &",
        text
    )

    text = _RE_STAR_SPACE.sub(
        " *",
        text
    )

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

        # -------------------------------------------------
        # Normal
        # -------------------------------------------------

        if state == "normal":

            # Line comment

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

            # Block comment

            if (
                ch == "/"
                and i + 1 < length
                and text[i + 1] == "*"
            ):

                result.append(" ")

                i += 2

                while i < length - 1:

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

            # String

            if ch == '"':

                state = "string"

                result.append(ch)

                i += 1

                continue

            # Character

            if ch == "'":

                state = "char"

                result.append(ch)

                i += 1

                continue

            result.append(ch)

            i += 1

            continue

        # -------------------------------------------------
        # String
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Character
        # -------------------------------------------------

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
# Split parameters
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

        elif ch == ")":

            if paren_depth > 0:
                paren_depth -= 1

            current.append(ch)

        elif ch == "[":

            bracket_depth += 1
            current.append(ch)

        elif ch == "]":

            if bracket_depth > 0:
                bracket_depth -= 1

            current.append(ch)

        elif ch == "{":

            brace_depth += 1
            current.append(ch)

        elif ch == "}":

            if brace_depth > 0:
                brace_depth -= 1

            current.append(ch)

        elif ch == "<":

            # Reasonable template detection.
            prev = parameters[i - 1] if i > 0 else ""
            nxt = parameters[i + 1] if i + 1 < length else ""

            if (
                nxt.isalnum()
                or nxt in "_>:*&"
                or prev.isalnum()
                or prev in "_>"
            ):

                angle_depth += 1

            current.append(ch)

        elif ch == ">":

            if angle_depth > 0:
                angle_depth -= 1

            current.append(ch)

        elif (
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

        else:

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
# Remove parameter name
# =========================================================

def remove_parameter_name(param):

    param = remove_default_value(
        param
    ).strip()

    if not param:
        return ""

    if param == "...":
        return "..."

    # -----------------------------------------------------
    # Function pointer/reference
    # -----------------------------------------------------

    param = re.sub(
        r'\(\s*[*&]\s*[A-Za-z_]\w*\s*\)',
        lambda m: (
            "(*)"
            if "*" in m.group(0)
            else "(&)"
        ),
        param
    )

    # -----------------------------------------------------
    # Array parameter
    # -----------------------------------------------------

    m = _RE_ARRAY_PARAM.match(param)

    if m:

        param = (
            m.group(1)
            + " "
            + m.group(3)
        )

    else:

        # -------------------------------------------------
        # Remove final identifier if it looks like a
        # parameter name.
        # -------------------------------------------------

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

    # -----------------------------------------------------
    # Normalize pointers/references
    # -----------------------------------------------------

    param = re.sub(
        r'\s*\*\s*',
        " *",
        param
    )

    param = re.sub(
        r'\s*&\s*',
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

    for param in split_parameters(
        parameters
    ):

        param = remove_parameter_name(
            param
        )

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
# Find function parameter range
# =========================================================

def find_function_parameter_range(
    declaration
):

    candidates = []

    bracket_depth = 0
    angle_depth = 0

    i = 0
    length = len(declaration)

    while i < length:

        ch = declaration[i]

        if ch == "[":

            bracket_depth += 1

        elif ch == "]":

            if bracket_depth > 0:
                bracket_depth -= 1

        elif ch == "<":

            angle_depth += 1

        elif ch == ">":

            if angle_depth > 0:
                angle_depth -= 1

        elif ch == "(":

            if (
                bracket_depth == 0
                and angle_depth == 0
            ):

                candidates.append(i)

        i += 1

    # -----------------------------------------------------
    # The function parameter list is normally the last
    # valid parenthesis pair in the declaration.
    # -----------------------------------------------------

    for start in reversed(candidates):

        end = find_matching_paren(
            declaration,
            start
        )

        if end < 0:
            continue

        prefix = declaration[
            :start
        ].strip()

        if not prefix:
            continue

        if _RE_CONTROL.match(
            prefix
        ):
            continue

        return start, end

    return -1, -1


# =========================================================
# Extract the actual function name
# =========================================================

def extract_name_from_prefix(prefix):

    prefix = clean_spaces(
        prefix
    )

    if not prefix:
        return None

    # =====================================================
    # OPERATOR
    #
    # Examples:
    #
    # Value::operator bool
    # Value::operator Hex
    # Value::operator int
    # Value::operator double
    # Value::operator=
    # operator==
    # =====================================================

    operator_pos = prefix.rfind(
        "operator"
    )

    if operator_pos >= 0:

        # Make sure "operator" is an identifier
        # and not part of another word.

        before_char = (
            prefix[operator_pos - 1]
            if operator_pos > 0
            else ""
        )

        after_pos = (
            operator_pos + len("operator")
        )

        after_char = (
            prefix[after_pos]
            if after_pos < len(prefix)
            else ""
        )

        valid_before = (
            not before_char
            or not (
                before_char.isalnum()
                or before_char == "_"
            )
        )

        valid_after = (
            not after_char
            or not (
                after_char.isalnum()
                or after_char == "_"
            )
        )

        if valid_before and valid_after:

            scope = prefix[
                :operator_pos
            ].strip()

            # -------------------------------------------------
            # Remove return type from scope.
            #
            # Example:
            #
            # bool Value::operator bool
            #
            # becomes:
            #
            # Value::
            # -------------------------------------------------

            scope_match = re.search(
                r'('
                r'(?:[A-Za-z_]\w*::)+'
                r')$',
                scope
            )

            if scope_match:

                scope = scope_match.group(1)

            else:

                scope = ""

            target = prefix[
                after_pos:
            ].strip()

            if not target:

                return (
                    scope
                    + "operator"
                )

            return (
                scope
                + "operator "
                + target
            ).strip()

    # =====================================================
    # Destructor
    #
    # Foo::~Foo
    # =====================================================

    destructor = re.search(
        r'((?:[A-Za-z_]\w*::)*'
        r'~[A-Za-z_]\w*)$',
        prefix
    )

    if destructor:

        return destructor.group(1)

    # =====================================================
    # Normal function
    #
    # We deliberately take the LAST qualified identifier.
    #
    # Example:
    #
    #   const std::vector<Value>& Property::GetValues
    #
    # -> Property::GetValues
    # =====================================================

    matches = list(
        re.finditer(
            r'[A-Za-z_]\w*'
            r'(?:\s*::\s*[A-Za-z_]\w*)*',
            prefix
        )
    )

    if not matches:
        return None

    candidate = matches[-1].group(0)

    candidate = clean_spaces(
        candidate
    )

    return candidate


# =========================================================
# Get function name
# =========================================================

def get_function_name(declaration):

    if not declaration:
        return None

    declaration = clean_spaces(
        declaration
    )

    start, end = find_function_parameter_range(
        declaration
    )

    if start < 0:
        return None

    prefix = declaration[
        :start
    ].strip()

    if not prefix:
        return None

    return extract_name_from_prefix(
        prefix
    )


# =========================================================
# Determine whether declaration is a function
# =========================================================

def looks_like_function(
    declaration
):

    if not declaration:
        return False

    declaration = clean_spaces(
        declaration
    )

    if "(" not in declaration:
        return False

    if ")" not in declaration:
        return False

    start, end = find_function_parameter_range(
        declaration
    )

    if start < 0 or end < 0:
        return False

    prefix = declaration[
        :start
    ].strip()

    if not prefix:
        return False

    # -----------------------------------------------------
    # Control structures
    # -----------------------------------------------------

    if _RE_CONTROL.match(
        prefix
    ):
        return False

    # -----------------------------------------------------
    # return/throw/case
    # -----------------------------------------------------

    if _RE_RETURN_THROW.search(
        prefix
    ):
        return False

    # -----------------------------------------------------
    # Lambda
    # -----------------------------------------------------

    if declaration.startswith("["):
        return False

    # -----------------------------------------------------
    # Assignment expressions.
    #
    # operator= is explicitly allowed.
    # -----------------------------------------------------

    if _RE_ASSIGNMENT.search(
        prefix
    ):

        if not _RE_ASSIGNMENT_OPERATOR.search(
            prefix
        ):

            return False

    # -----------------------------------------------------
    # Macro invocation
    # -----------------------------------------------------

    if _RE_UPPERCASE_MACRO.fullmatch(
        declaration
    ):

        return False

    # -----------------------------------------------------
    # Function name
    # -----------------------------------------------------

    name = get_function_name(
        declaration
    )

    if not name:
        return False

    # -----------------------------------------------------
    # Operators
    # -----------------------------------------------------

    if "operator" in name:

        return True

    # -----------------------------------------------------
    # Qualified member function
    # -----------------------------------------------------

    if "::" in name:

        return True

    # -----------------------------------------------------
    # Normal function.
    #
    # We need something before the final function name
    # that looks like a return type.
    # -----------------------------------------------------

    name_match = re.search(
        r'([A-Za-z_]\w*)$',
        name
    )

    if not name_match:
        return False

    function_name = name_match.group(1)

    # -----------------------------------------------------
    # Locate the function name at the end of prefix.
    # -----------------------------------------------------

    function_match = re.search(
        r'([A-Za-z_]\w*)\s*$',
        prefix
    )

    if not function_match:
        return False

    before_name = prefix[
        :function_match.start()
    ].strip()

    if not before_name:

        # This can be a constructor/function with no
        # explicit return type only if qualified.
        return "::" in name

    # -----------------------------------------------------
    # Reject obvious expressions.
    # -----------------------------------------------------

    if re.search(
        r'[=+\-/!|^.]',
        before_name
    ):

        return False

    if "[" in before_name:
        return False

    if "]" in before_name:
        return False

    return_type = before_name

    # -----------------------------------------------------
    # Remove pointer/reference qualifiers.
    # -----------------------------------------------------

    test_type = re.sub(
        r'[\*&]',
        " ",
        return_type
    )

    test_type = clean_spaces(
        test_type
    )

    if not test_type:
        return False

    # -----------------------------------------------------
    # A return type should contain identifiers, scope,
    # templates and common type qualifiers.
    #
    # This is intentionally permissive.
    # -----------------------------------------------------

    if not re.fullmatch(
        r'(?:'
        r'const\s+|volatile\s+|'
        r'unsigned\s+|signed\s+|'
        r'long\s+|short\s+|'
        r'class\s+|struct\s+|enum\s+|'
        r'typename\s+|'
        r')*'
        r'[A-Za-z_]\w*'
        r'(?:\s*::\s*[A-Za-z_]\w*)*'
        r'(?:\s*<[^{}();]*>)?',
        test_type
    ):

        return False

    return True


# =========================================================
# Normalize complete function declaration
# =========================================================

def normalize_function(
    declaration
):

    declaration = clean_spaces(
        declaration
    )

    declaration = declaration.rstrip()

    if declaration.endswith("{"):

        declaration = declaration[
            :-1
        ].strip()

    declaration = declaration.rstrip(
        ";"
    ).strip()

    if not declaration:
        return None

    start, end = find_function_parameter_range(
        declaration
    )

    if start < 0 or end < 0:
        return None

    before = declaration[
        :start
    ].strip()

    parameters = declaration[
        start + 1:end
    ].strip()

    after = declaration[
        end + 1:
    ].strip()

    parameters = remove_parameter_names(
        parameters
    )

    result = (
        before
        + "("
        + parameters
        + ")"
    )

    if after:

        result += " " + after

    result += ";"

    return clean_spaces(
        result
    )


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

        cond = bool(cond)

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

        if len(stack) <= 1:
            return True

        level = stack[-1]

        if level["taken"]:

            level["active"] = False

        else:

            cond = bool(
                eval_pp_expr(
                    m.group(1),
                    defines
                )
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
# Find function brace
# =========================================================

def find_function_brace(
    line
):

    position = line.rfind(
        "{"
    )

    if position < 0:
        return -1

    prefix = line[
        :position
    ].strip()

    if not prefix:
        return -1

    if "(" not in prefix:
        return -1

    if ")" not in prefix:
        return -1

    if looks_like_function(
        prefix
    ):

        return position

    return -1


# =========================================================
# Append implementation
# =========================================================

def append_function(
    functions,
    filename,
    relative_path,
    normalized
):

    name = get_function_name(
        normalized
    )

    if not name:
        return

    functions.append(
        {
            "file":
                os.path.basename(
                    filename
                ),

            "path":
                relative_path,

            "name":
                name,

            "declaration":
                normalized
        }
    )


# =========================================================
# Parse one C/C++ file
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

    except (
        FileNotFoundError,
        OSError
    ):

        return

    text = remove_comments(
        text
    )

    lines = text.splitlines()

    stack = [
        {
            "parent": True,
            "active": True,
            "taken": False
        }
    ]

    function_depth = 0

    declaration = ""

    i = 0
    total_lines = len(lines)

    while i < total_lines:

        if (
            verbose
            and i % 500 == 0
        ):

            print(
                f"Parsing line "
                f"{i + 1}/{total_lines} "
                f"in {filename}",
                flush=True
            )

        raw = lines[i]

        line = raw.strip()

        i += 1

        if not line:
            continue

        # =================================================
        # Preprocessor
        # =================================================

        if line.startswith("#"):

            process_condition(
                line,
                stack,
                defines,
                eval_pp_expr
            )

            continue

        # =================================================
        # Inactive branch
        # =================================================

        if not stack[-1]["active"]:
            continue

        # =================================================
        # Function body
        # =================================================

        if function_depth > 0:

            function_depth += line.count(
                "{"
            )

            function_depth -= line.count(
                "}"
            )

            if function_depth <= 0:

                function_depth = 0
                declaration = ""

            continue

        # =================================================
        # Closing brace
        # =================================================

        if line == "}":

            declaration = ""

            continue

        if line.startswith("}"):

            declaration = ""

            continue

        # =================================================
        # Ignore obvious macros
        # =================================================

        if _RE_UPPERCASE_MACRO.fullmatch(
            line
        ):

            declaration = ""

            continue

        # =================================================
        # Accumulate declaration
        # =================================================

        if declaration:

            declaration += " "

        declaration += line

        # =================================================
        # No opening brace
        # =================================================

        if "{" not in line:

            # -------------------------------------------------
            # A declaration ending in ';' is not an
            # implementation.
            # -------------------------------------------------

            if ";" in line:

                declaration = ""

            continue

        # =================================================
        # Opening brace
        # =================================================

        brace_position = find_function_brace(
            declaration
        )

        if brace_position >= 0:

            header = declaration[
                :brace_position
            ].strip()

            if looks_like_function(
                header
            ):

                normalized = normalize_function(
                    header
                )

                if normalized:

                    append_function(
                        functions,
                        filename,
                        relative_path,
                        normalized
                    )

                remaining = declaration[
                    brace_position:
                ]

                opens = remaining.count(
                    "{"
                )

                closes = remaining.count(
                    "}"
                )

                function_depth = (
                    opens - closes
                )

                if function_depth < 0:

                    function_depth = 0

                declaration = ""

                continue

        # =================================================
        # Non-function brace
        #
        # class
        # struct
        # namespace
        # enum
        # initializer
        # =================================================

        opens = declaration.count(
            "{"
        )

        closes = declaration.count(
            "}"
        )

        if opens or closes:

            declaration = ""

        elif ";" in line:

            declaration = ""


# =========================================================
# Parse implementation directory
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

        dirs[:] = [
            d
            for d in dirs
            if d not in {
                ".git",
                ".svn",
                "build",
                "cmake-build-debug",
                "cmake-build-release"
            }
        ]

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

            visited.add(
                filename
            )

            relative_path = os.path.relpath(
                filename,
                project_root
            )

            if verbose:

                print(
                    f"Parsing C/C++ file: "
                    f"{filename}",
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
# Print implementations
# =========================================================

def print_implementations(
    functions
):

    for item in functions:

        print(
            f"{item['name']:35} "
            f"{item['file']:25} "
            f"{item['path']:45} "
            f"{item['declaration']}"
        )