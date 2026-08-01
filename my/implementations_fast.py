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
    r'explicit|mutable|register|const|volatile|typename)\b'
)

_RE_NESTED_CALL = re.compile(
    r'\([^()]*\)'
)

_RE_FUNCTION_POINTER_NAME = re.compile(
    r'\(\s*[*&]\s*([A-Za-z_]\w*)\s*\)'
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

# ---------------------------------------------------------
# C++ operator names
#
# Important:
#
# operator bool
# operator Hex
# operator int
# operator double
#
# are conversion operators and must be accepted.
# ---------------------------------------------------------

_RE_OPERATOR_NAME = re.compile(
    r'((?:[A-Za-z_]\w*::)*'
    r'operator\s*'
    r'(?:'
        r'new(?:\[\])?'
        r'|delete(?:\[\])?'
        r'|<<=?'
        r'|>>=?'
        r'|=='
        r'|!='
        r'|<='
        r'|>='
        r'|\+\+'
        r'|--'
        r'|&&'
        r'|\|\|'
        r'|->\*'
        r'|->'
        r'|\+'
        r'|-'
        r'|\*'
        r'|/'
        r'|%'
        r'|&'
        r'|\|'
        r'|\^'
        r'|~'
        r'|!'
        r'|='
        r'|<'
        r'|>'
        r'|\(\)'
        r'|\[\]'
        r'|[A-Za-z_]\w*'
    r'))$'
)

_RE_DESTRUCTOR_NAME = re.compile(
    r'((?:[A-Za-z_]\w*::)*~[A-Za-z_]\w*)$'
)

_RE_NORMAL_FUNCTION_NAME = re.compile(
    r'((?:[A-Za-z_]\w*::)*[A-Za-z_]\w*)$'
)

# ---------------------------------------------------------
# Types
# ---------------------------------------------------------

_RE_TYPE = re.compile(
    r'^(?:(?:const\s+|volatile\s+|unsigned\s+|signed\s+|'
    r'long\s+|short\s+)*'
    r'[A-Za-z_]\w*'
    r'(?:\s*::\s*[A-Za-z_]\w*)*'
    r'(?:\s*<[^;{}()]*>)?'
    r'(?:\s*[\*&]+)?)$'
)

# ---------------------------------------------------------
# Qualified function name
# ---------------------------------------------------------

_RE_QUALIFIED_NAME = re.compile(
    r'(?:[A-Za-z_]\w*::)+'
    r'~?[A-Za-z_]\w*$'
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

            # -------------------------------------------------
            # Line comment
            # -------------------------------------------------

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

            # -------------------------------------------------
            # Block comment
            # -------------------------------------------------

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

            # -------------------------------------------------
            # String
            # -------------------------------------------------

            if ch == '"':

                state = "string"
                result.append(ch)
                i += 1

                continue

            # -------------------------------------------------
            # Character
            # -------------------------------------------------

            if ch == "'":

                state = "char"
                result.append(ch)
                i += 1

                continue

            result.append(ch)
            i += 1

            continue

        # =====================================================
        # String
        # =====================================================

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

        # =====================================================
        # Character
        # =====================================================

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

        # -----------------------------------------------------
        # Template angle brackets
        # -----------------------------------------------------

        if ch == "<":

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
            i += 1
            continue

        if ch == ">":

            if angle_depth > 0:
                angle_depth -= 1

            current.append(ch)
            i += 1
            continue

        # -----------------------------------------------------
        # Parameter separator
        # -----------------------------------------------------

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

    param = remove_default_value(param)
    param = param.strip()

    if not param:
        return ""

    if param == "...":
        return "..."

    # -----------------------------------------------------
    # Function pointer
    # -----------------------------------------------------

    m = _RE_FUNCTION_POINTER_NAME.search(param)

    if m:

        param = _RE_FUNCTION_POINTER.sub(
            "(*)",
            param
        )

    # -----------------------------------------------------
    # Function reference
    # -----------------------------------------------------

    param = _RE_FUNCTION_REFERENCE.sub(
        "(&)",
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
    # Normalize pointer/reference spacing
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

    paren_depth = 0
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

            if bracket_depth == 0 and angle_depth == 0:
                candidates.append(i)

        i += 1

    # -----------------------------------------------------
    # Prefer the last candidate.
    #
    # This is important for declarations containing
    # templates or nested constructs.
    # -----------------------------------------------------

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
        # Do not accept an arbitrary expression such as:
        #
        # foo(bar)
        #
        # unless it looks like a function declaration.
        # -------------------------------------------------

        if _RE_CONTROL.match(prefix):
            continue

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

    parameters = remove_parameter_names(
        parameters
    )

    suffix = ""

    if after:
        suffix = " " + after

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

    # -----------------------------------------------------
    # Assignment expressions are not declarations.
    #
    # Exception: operator=
    # -----------------------------------------------------

    if _RE_ASSIGNMENT.search(prefix):

        if not _RE_ASSIGNMENT_OPERATOR.search(prefix):
            return None

    # -----------------------------------------------------
    # Conversion / overloaded operators
    # -----------------------------------------------------

    m = _RE_OPERATOR_NAME.search(prefix)

    if m:
        return m.group(1)

    # -----------------------------------------------------
    # Destructor
    # -----------------------------------------------------

    m = _RE_DESTRUCTOR_NAME.search(prefix)

    if m:
        return m.group(1)

    # -----------------------------------------------------
    # Normal / qualified function
    # -----------------------------------------------------

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
    # Reject control structures
    # =====================================================

    if _RE_CONTROL.match(prefix):
        return False

    # =====================================================
    # Reject return / throw / case expressions
    # =====================================================

    if _RE_RETURN_THROW.search(prefix):
        return False

    # =====================================================
    # Lambda
    # =====================================================

    if declaration.startswith("["):
        return False

    # =====================================================
    # Assignment expressions
    # =====================================================

    if _RE_ASSIGNMENT.search(prefix):

        if not _RE_ASSIGNMENT_OPERATOR.search(prefix):
            return False

    # =====================================================
    # Operator overloads
    # =====================================================

    if "operator" in prefix:

        # Conversion operators:
        #
        #   Value::operator bool()
        #   Value::operator Hex()
        #   Value::operator int()
        #   Value::operator double()
        #
        # and ordinary operators are all valid.
        #
        return bool(
            _RE_OPERATOR_NAME.search(prefix)
        )

    # =====================================================
    # Arithmetic expression rejection
    # =====================================================

    if _RE_ARITHMETIC.search(prefix):

        return False

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
    # Extract function name
    # =====================================================

    name = get_function_name(
        declaration
    )

    if not name:
        return False

    # =====================================================
    # Qualified/member function
    #
    # Examples:
    #
    #   DOS_File::operator=
    #   Value::operator bool
    #   Foo::Bar
    #   Foo::~Foo
    # =====================================================

    if "::" in name:

        if _RE_QUALIFIED_NAME.fullmatch(name):

            return True

    # =====================================================
    # Explicit operator
    # =====================================================

    if name.startswith("operator"):

        return True

    # =====================================================
    # Locate final identifier
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
    # Qualified scope in prefix
    # =====================================================

    if "::" in before_name:

        if "=" in before_name:
            return False

        # A scope ending in :: is strong evidence of a
        # member/qualified function.
        if re.search(
            r'(?:^|[\s*&])'
            r'(?:[A-Za-z_]\w*)'
            r'(?:\s*::\s*[A-Za-z_]\w*)*'
            r'\s*::\s*$',
            before_name
        ):

            return True

    # =====================================================
    # Return type
    # =====================================================

    return_type = before_name

    if not return_type:
        return False

    # -----------------------------------------------------
    # Expressions cannot be return types.
    # -----------------------------------------------------

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

    if not _RE_TYPE.fullmatch(
        type_for_validation
    ):

        return False

    # =====================================================
    # Additional assignment protection
    # =====================================================

    if _RE_ASSIGNMENT_NAME.search(
        declaration
    ):

        if not _RE_ASSIGNMENT_OPERATOR.search(
            declaration
        ):

            return False

    # =====================================================
    # Reject nested function calls in prefix
    # =====================================================

    inner_prefix = declaration[:start]

    # Remove the actual function name from consideration.
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

        stack.append(
            {
                "parent":
                    stack[-1]["active"],

                "active":
                    stack[-1]["active"] and cond,

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

        cond = m.group(1) not in defines

        stack.append(
            {
                "parent":
                    stack[-1]["active"],

                "active":
                    stack[-1]["active"] and cond,

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
                    stack[-1]["active"] and cond,

                "taken":
                    bool(cond)
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
# Determine whether a brace belongs to a function
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

    # -----------------------------------------------------
    # Function declarations ending in ';' are not bodies.
    # -----------------------------------------------------

    if after_close.endswith(";"):
        return -1

    if looks_like_function(prefix):
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
                os.path.basename(filename),

            "path":
                relative_path,

            "name":
                name,

            "declaration":
                normalized
        }
    )


# =========================================================
# Parse one C/C++ implementation/header file
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

        if verbose and i % 500 == 0:

            print(
                f"Parsing line {i + 1}/{total_lines} "
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
        # Inactive preprocessor branch
        # =================================================

        if not stack[-1]["active"]:
            continue

        # =================================================
        # Inside function body
        # =================================================

        if function_depth > 0:

            function_depth += line.count("{")
            function_depth -= line.count("}")

            if function_depth <= 0:

                function_depth = 0
                declaration = ""

            continue

        # =================================================
        # Standalone closing brace
        # =================================================

        if line == "}":

            declaration = ""
            continue

        # =================================================
        # Closing brace followed by something
        # =================================================

        if line.startswith("}"):

            line = _RE_WHILE_AFTER_BRACE.sub(
                "",
                line
            ).strip()

            declaration = ""

            if not line:
                continue

        # =================================================
        # Ignore obvious macro invocations
        # =================================================

        if _RE_UPPERCASE_MACRO.match(line):

            declaration = ""
            continue

        # =================================================
        # Accumulate declaration
        # =================================================

        if declaration:
            declaration += " "

        declaration += line

        # =================================================
        # No brace:
        #
        # Only a semicolon can terminate this declaration.
        # =================================================

        if "{" not in line:

            if ";" in line:
                declaration = ""

            continue

        # =================================================
        # Brace exists.
        # =================================================

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

                    append_function(
                        functions,
                        filename,
                        relative_path,
                        normalized
                    )

                # -----------------------------------------
                # Enter function body.
                # -----------------------------------------

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

        # =================================================
        # Non-function brace
        #
        # class / struct / namespace / enum / initializer
        # =================================================

        opens = declaration.count("{")
        closes = declaration.count("}")

        if opens or closes:

            declaration = ""

        elif ";" in line:

            declaration = ""


# =========================================================
# Parse directory with C/C++ implementations
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

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # .h/.hpp are included because DOSBox-X contains real
    # inline implementations there, for example:
    #
    #   writeString()
    #   readString()
    #
    # Declarations ending in ';' are still ignored.
    # -----------------------------------------------------

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

        # -------------------------------------------------
        # Avoid common generated/build directories.
        # -------------------------------------------------

        dirs[:] = [
            d for d in dirs
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

            visited.add(filename)

            relative_path = os.path.relpath(
                filename,
                project_root
            )

            if verbose:

                print(
                    f"Parsing C/C++ file: {filename}",
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
# Optional helper: print results
# =========================================================

def print_implementations(functions):

    for item in functions:

        print(
            f"{item['name']:35} "
            f"{item['file']:25} "
            f"{item['path']:45} "
            f"{item['declaration']}"
        )