# implementations.py

import os
import re


# =========================================================
# Normalize spaces
# =========================================================

def clean_spaces(text):

    text = " ".join(text.split())

    text = re.sub(
        r'\s+\)',
        ')',
        text
    )

    text = re.sub(
        r'\(\s+',
        '(',
        text
    )

    text = re.sub(
        r'\s*,\s*',
        ', ',
        text
    )

    text = re.sub(
        r'\s*::\s*',
        '::',
        text
    )

    text = re.sub(
        r'\s*&\s*',
        ' &',
        text
    )

    text = re.sub(
        r'\s+\*',
        ' *',
        text
    )

    return text.strip()


# =========================================================
# Remove comments
#
# This version understands:
#
#   // comments
#   /* comments */
#
# while preserving strings and character literals.
# =========================================================

def remove_comments(text):

    result = []

    i = 0
    length = len(text)

    state = "normal"

    while i < length:

        ch = text[i]

        # -------------------------------------------------
        # Normal code
        # -------------------------------------------------

        if state == "normal":

            # C++ line comment
            if ch == "/" and i + 1 < length and text[i + 1] == "/":

                result.append(" ")

                i += 2

                while i < length and text[i] != "\n":
                    i += 1

                continue

            # C/C++ block comment
            if ch == "/" and i + 1 < length and text[i + 1] == "*":

                result.append(" ")

                i += 2

                while i + 1 < length:

                    if text[i] == "*" and text[i + 1] == "/":

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

                    result.append(text[i + 1])

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

                    result.append(text[i + 1])

                    i += 2

                    continue

            if ch == "'":

                state = "normal"

            i += 1

            continue

    return "".join(result)


# =========================================================
# Split a C++ parameter list
#
# This is important because:
#
#   std::vector<int, std::allocator<int>>
#
# contains commas that are NOT parameter separators.
#
# We therefore split only on commas at the top level.
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

        # -------------------------------------------------
        # Parentheses
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Arrays
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Braces
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Template brackets
        # -------------------------------------------------

        if ch == "<":

            # Heuristic:
            # treat < as template opening when followed by
            # something that looks like a type.
            next_char = ""

            if i + 1 < len(parameters):
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

        # -------------------------------------------------
        # Parameter separator
        # -------------------------------------------------

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
#
# Example:
#
#   int count = 10
#
# becomes:
#
#   int count
#
# =========================================================

def remove_default_value(param):

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
# Remove parameter variable name
#
# Examples:
#
#   int value
#       -> int
#
#   const char *text
#       -> const char *
#
#   std::string &name
#       -> std::string &
#
#   int values[]
#       -> int []
#
# =========================================================

def remove_parameter_name(param):

    param = remove_default_value(param)

    param = param.strip()

    if not param:

        return ""

    if param == "...":

        return "..."

    # -----------------------------------------------------
    # Function pointer parameter
    #
    # Example:
    #
    #   void (*callback)(int)
    #
    # Keep the type structure but remove callback.
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
    #
    #   int values[]
    #
    #   int values[10]
    #
    # becomes:
    #
    #   int []
    #
    # -----------------------------------------------------

    m = re.match(
        r'^(.*?)(?:\s+)([A-Za-z_]\w*)\s*(\[[^\]]*\])$',
        param
    )

    if m:

        param = (
            m.group(1)
            + " "
            + m.group(3)
        )

    else:

        # -------------------------------------------------
        # Normal parameter
        #
        # Remove only a final identifier.
        #
        # This is safer for C++ because identifiers can
        # occur inside templates.
        # -------------------------------------------------

        m = re.match(
            r'^(.*\S)\s+([A-Za-z_]\w*)$',
            param
        )

        if m:

            before = m.group(1)

            name = m.group(2)

            # -------------------------------------------------
            # Do not remove obvious C++ keywords/types.
            # -------------------------------------------------

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
        ' *',
        param
    )

    param = re.sub(
        r'\s*&\s*',
        ' &',
        param
    )

    param = clean_spaces(param)

    return param


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

    while i < len(text):

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

    # -----------------------------------------------------
    # Search for a '(' that belongs to a function name.
    #
    # We search from left to right but use the last valid
    # candidate. This helps with:
    #
    #   std::function<void(int)>
    #
    # and similar C++ declarations.
    # -----------------------------------------------------

    candidates = []

    depth = 0

    i = 0

    while i < len(declaration):

        ch = declaration[i]

        if ch == "<":

            depth += 1

        elif ch == ">":

            if depth > 0:
                depth -= 1

        elif ch == "(":

            if depth == 0:

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
        # The text immediately before '(' should end in a
        # function identifier, qualified name, destructor,
        # or operator.
        # -------------------------------------------------

        if re.search(
            r'(?:[A-Za-z_~]\w*|operator\s*\S+|\))$',
            prefix
        ):

            return start, end

    return -1, -1


# =========================================================
# Normalize function declaration
# =========================================================

def normalize_function(declaration):

    declaration = clean_spaces(
        declaration
    )

    # -----------------------------------------------------
    # Remove opening brace
    # -----------------------------------------------------

    declaration = declaration.rstrip()

    if declaration.endswith("{"):

        declaration = declaration[:-1].strip()

    # -----------------------------------------------------
    # Remove trailing semicolon
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # A function definition may have:
    #
    #   const
    #   noexcept
    #   override
    #   final
    #
    # Keep these.
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # Reject obvious expressions / function calls.
    #
    # Example:
    #
    #     double rtnow = PIC_FullIndex();
    #
    # must NOT produce:
    #
    #     PIC_FullIndex
    #
    # -----------------------------------------------------

    raw = declaration.strip()

    # Assignment before the opening parenthesis means this
    # is an expression, not a function declaration.
    #
    # Example:
    #
    #     double rtnow = PIC_FullIndex()
    #
    first_paren = raw.find("(")

    if first_paren >= 0:

        before_paren = raw[:first_paren]

        if "=" in before_paren:

            return None

    # -----------------------------------------------------
    # Normalize whitespace.
    # -----------------------------------------------------

    declaration = clean_spaces(
        declaration
    )

    start, end = find_function_parameter_range(
        declaration
    )

    if start < 0:

        return None

    prefix = declaration[:start].strip()

    if not prefix:

        return None

    # -----------------------------------------------------
    # Reject assignments after normalization as well.
    # -----------------------------------------------------

    if "=" in prefix:

        return None

    # -----------------------------------------------------
    # Reject obvious control statements.
    # -----------------------------------------------------

    forbidden = {
        "if",
        "else",
        "while",
        "for",
        "switch",
        "catch",
        "return"
    }

    first_word = re.match(
        r'^([A-Za-z_]\w*)',
        prefix
    )

    if first_word:

        if first_word.group(1) in forbidden:

            return None

    # -----------------------------------------------------
    # C++ operator overload
    #
    #   MyClass::operator=(...)
    #   operator<<(...)
    # -----------------------------------------------------

    m = re.search(
        r'((?:[A-Za-z_~]\w*::)*operator\s*(?:'
        r'new|delete|new\[\]|delete\[\]|'
        r'<<=|>>=|<<|>>|==|!=|<=|>=|'
        r'\+\+|--|&&|\|\||->\*|->|'
        r'\+|-|\*|/|%|&|\||\^|'
        r'~|!|=|<|>|'
        r'\(\)|\[\]'
        r'))$',
        prefix
    )

    if m:

        return m.group(1)

    # -----------------------------------------------------
    # Destructor
    #
    #   Foo::~Foo(...)
    # -----------------------------------------------------

    m = re.search(
        r'((?:[A-Za-z_]\w*::)*~[A-Za-z_]\w*)$',
        prefix
    )

    if m:

        return m.group(1)

    # -----------------------------------------------------
    # Normal / qualified function
    #
    #   function
    #   Foo::function
    #   A::B::function
    # -----------------------------------------------------

    m = re.search(
        r'((?:[A-Za-z_]\w*::)*[A-Za-z_]\w*)$',
        prefix
    )

    if m:

        return m.group(1)

    return None

# =========================================================
# Determine whether a declaration is a function
# =========================================================

def looks_like_function(declaration):

    if not declaration:

        return False

    declaration = declaration.strip()

    if not declaration:

        return False

    # -----------------------------------------------------
    # Normalize whitespace
    # -----------------------------------------------------

    declaration = clean_spaces(
        declaration
    )

    if not declaration:

        return False

    # -----------------------------------------------------
    # Must contain a parameter list
    # -----------------------------------------------------

    start, end = find_function_parameter_range(
        declaration
    )

    if start < 0 or end < 0:

        return False

    prefix = declaration[:start].strip()

    if not prefix:

        return False

    # =====================================================
    # HARD REJECT: assignments / initializers
    #
    #   double rtnow = PIC_FullIndex()
    #   DynReg * di_base = DREG(ES)
    #   name = new char[...]
    #   ext.attribute = real_readw(...)
    #   rep_ecx_jmp = gen_create_branch_long(...)
    #
    # =====================================================

    if re.search(
        r'(?<![=!<>])=(?!=)',
        prefix
    ):

        # The only valid assignment-looking construct here
        # is an overloaded operator:
        #
        #   operator=(...)
        #   Foo::operator=(...)
        #
        if not re.search(
            r'\boperator\s*=',
            prefix
        ):

            return False

    # =====================================================
    # HARD REJECT: obvious expressions
    # =====================================================

    if re.search(
        r'\b(?:return|throw|case)\b',
        prefix
    ):

        return False

    # -----------------------------------------------------
    # Reject arithmetic/logical expressions
    # -----------------------------------------------------

    if re.search(
        r'(?<!:)[+\-/%!|^](?!>)',
        prefix
    ):

        # Operator overloads are handled separately below.
        if "operator" not in prefix:

            return False

    # =====================================================
    # Reject control statements
    # =====================================================

    if re.match(
        r'^\s*(?:'
        r'if|'
        r'else|'
        r'for|'
        r'while|'
        r'switch|'
        r'catch|'
        r'do'
        r')\b',
        prefix
    ):

        return False

    # =====================================================
    # Reject lambdas
    #
    #   [](...)
    #   [this](...)
    #   [x](...)
    # =====================================================

    if declaration.startswith("["):

        return False

    # =====================================================
    # Reject obvious standalone function calls
    #
    #   GetTicks()
    #   PIC_FullIndex()
    #   DREG(ES)
    #   gen_protectflags()
    #
    # =====================================================

    # Remove declaration qualifiers first.
    # -----------------------------------------------------

    test_prefix = re.sub(
        r'\b(?:'
        r'virtual|'
        r'static|'
        r'inline|'
        r'extern|'
        r'constexpr|'
        r'consteval|'
        r'friend|'
        r'explicit|'
        r'mutable|'
        r'register|'
        r'const|'
        r'volatile'
        r')\b',
        ' ',
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
    # C++ operator overload
    #
    #   operator=(...)
    #   operator<<(...)
    #   operator bool(...)
    # =====================================================

    if re.search(
        r'\boperator\b',
        prefix
    ):

        return True

    # =====================================================
    # Find final function identifier
    # =====================================================

    name_match = re.search(
        r'([A-Za-z_]\w*)$',
        test_prefix
    )

    if not name_match:

        return False

    function_name = name_match.group(1)

    before_name = test_prefix[
        :name_match.start()
    ].strip()

    # =====================================================
    # Standalone call detection
    #
    #   GetTicks
    #   DREG
    #   gen_protectflags
    #
    # No return type exists.
    # =====================================================

    if not before_name:

        return False

    # =====================================================
    # C++ scoped/member function
    #
    #   Foo::bar(...)
    #   A::B::bar(...)
    #   Foo::~Foo(...)
    #
    # For these, verify that the prefix before the name
    # actually contains a valid type or scope.
    # =====================================================

    if "::" in before_name:

        # Remove the scope from the declaration and inspect
        # what remains before the function name.
        #
        # Example:
        #
        #   void A::B::foo
        #
        # becomes:
        #
        #   void A::B::
        #
        scoped_prefix = before_name

        if re.search(
            r'[=]',
            scoped_prefix
        ):

            return False

        # A scope-only expression such as:
        #
        #   object::foo(...)
        #
        # is ambiguous, but a qualified definition such as:
        #
        #   void A::foo(...)
        #
        # has a return type before the scope.
        #
        # Constructors/destructors are the exception.

        if re.search(
            r'(?:^|[\s*&])'
            r'(?:[A-Za-z_]\w*)'
            r'\s*::\s*$',
            scoped_prefix
        ):

            # Check whether this looks like a constructor or
            # destructor declaration.
            if re.search(
                r'(?:^|::)~?[A-Za-z_]\w*\s*::\s*$',
                scoped_prefix
            ):

                return True

        # There must be a declaration type before the scope.
        if not re.search(
            r'\b(?:'
            r'void|'
            r'bool|'
            r'char|'
            r'short|'
            r'int|'
            r'long|'
            r'float|'
            r'double|'
            r'unsigned|'
            r'signed|'
            r'[A-Za-z_]\w*'
            r')\b',
            scoped_prefix
        ):

            return False

    # =====================================================
    # Everything before the function name is the return
    # type / declaration type.
    # =====================================================

    return_type = before_name

    if not return_type:

        return False

    # =====================================================
    # Reject expression syntax in return type
    # =====================================================

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
    # Remove C++ pointer/reference symbols for validation
    # =====================================================

    type_for_validation = re.sub(
        r'[\*&]',
        ' ',
        return_type
    )

    type_for_validation = clean_spaces(
        type_for_validation
    )

    if not type_for_validation:

        return False

    # =====================================================
    # Validate declaration type
    #
    # Examples:
    #
    #   void Foo(...)
    #   int Foo(...)
    #   Bitu Foo(...)
    #   DynReg * Foo(...)
    #   DOS_File & Foo(...)
    #   const char * Foo(...)
    #   std::string Foo(...)
    #
    # =====================================================

    type_pattern = re.compile(
        r'^(?:'
        r'(?:const\s+|volatile\s+|unsigned\s+|signed\s+|'
        r'long\s+|short\s+)*'
        r'[A-Za-z_]\w*'
        r'(?:\s*::\s*[A-Za-z_]\w*)*'
        r'(?:\s*<[^;{}()]*>)?'
        r'(?:\s*[\*&]+)?'
        r')$'
    )

    if not type_pattern.fullmatch(
        type_for_validation
    ):

        return False

    # =====================================================
    # IMPORTANT:
    #
    # Reject the classic false-positive:
    #
    #   DynReg * di_base = DREG(ES)
    #
    # At this point the assignment check above should already
    # have rejected it.
    #
    # This additional check protects against malformed input
    # where '=' was removed before reaching this function.
    # =====================================================

    if re.search(
        r'\b[A-Za-z_]\w*\s*=\s*',
        declaration
    ):

        if not re.search(
            r'\boperator\s*=',
            declaration
        ):

            return False

    # =====================================================
    # Reject declarations that contain another function call
    # before the candidate function name.
    #
    # Example:
    #
    #   Type variable = DREG(...)
    #
    # =====================================================

    inner_prefix = declaration[:start]

    # Remove the candidate function name itself.
    inner_prefix = re.sub(
        r'[A-Za-z_]\w*\s*$',
        '',
        inner_prefix
    ).strip()

    # Any remaining (...) means we have a nested call,
    # not a normal function declaration.
    if re.search(
        r'\([^()]*\)',
        inner_prefix
    ):

        return False

    # =====================================================
    # Passed all checks
    # =====================================================

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

    # -----------------------------------------------------
    # #ifdef
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # #ifndef
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # #if
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # #elif
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # #else
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # #endif
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Scan the text while respecting:
    #
    #   ()
    #   []
    #   <>
    #   strings
    #   characters
    #
    # Braces are candidates only when we are not inside
    # parentheses or brackets.
    # -----------------------------------------------------

    paren = 0
    bracket = 0
    angle = 0

    string = False
    char = False
    escape = False

    candidates = []

    i = 0

    while i < len(line):

        ch = line[i]

        # -------------------------------------------------
        # String
        # -------------------------------------------------

        if string:

            if escape:
                escape = False

            elif ch == "\\":
                escape = True

            elif ch == '"':
                string = False

            i += 1
            continue

        # -------------------------------------------------
        # Character
        # -------------------------------------------------

        if char:

            if escape:
                escape = False

            elif ch == "\\":
                escape = True

            elif ch == "'":
                char = False

            i += 1
            continue

        # -------------------------------------------------
        # Start string / character
        # -------------------------------------------------

        if ch == '"':
            string = True
            i += 1
            continue

        if ch == "'":
            char = True
            i += 1
            continue

        # -------------------------------------------------
        # Parentheses
        # -------------------------------------------------

        if ch == "(":

            paren += 1

        elif ch == ")":

            if paren > 0:
                paren -= 1

        # -------------------------------------------------
        # Brackets
        # -------------------------------------------------

        elif ch == "[":

            bracket += 1

        elif ch == "]":

            if bracket > 0:
                bracket -= 1

        # -------------------------------------------------
        # Angle brackets
        # -------------------------------------------------

        elif ch == "<":

            angle += 1

        elif ch == ">":

            if angle > 0:
                angle -= 1

        # -------------------------------------------------
        # Candidate brace
        # -------------------------------------------------

        elif ch == "{":

            if paren == 0 and bracket == 0:

                candidates.append(i)

        i += 1

    # -----------------------------------------------------
    # Check candidates from right to left.
    #
    # IMPORTANT:
    #
    # Do a cheap test before calling looks_like_function().
    # This prevents expensive regex processing for braces
    # that obviously cannot belong to a function.
    # -----------------------------------------------------

    for position in reversed(candidates):

        prefix = line[:position].strip()

        # -------------------------------------------------
        # A function definition must contain '(' before
        # the candidate brace.
        # -------------------------------------------------

        if "(" not in prefix:

            continue

        # -------------------------------------------------
        # A function definition normally has ')' before
        # the body brace.
        # -------------------------------------------------

        if ")" not in prefix:

            continue

        # -------------------------------------------------
        # Avoid testing enormous unrelated prefixes.
        #
        # If there is another complete statement after the
        # closing ')' then this brace is unlikely to be the
        # function body.
        # -------------------------------------------------

        last_close = prefix.rfind(")")

        if last_close < 0:

            continue

        after_close = prefix[last_close + 1:].strip()

        # -------------------------------------------------
        # Valid function definitions can have:
        #
        #   const
        #   noexcept
        #   override
        #   final
        #   = delete
        #   = default
        #   -> return_type
        #   initializer lists beginning with :
        #
        # so do not reject these here.
        #
        # We only reject obvious statement terminators.
        # -------------------------------------------------

        if after_close.endswith(";"):

            continue

        if looks_like_function(prefix):

            return position

    return -1


# =========================================================
# Parse one C++ implementation file
# =========================================================

def parse_cpp_file(
    filename,
    relative_path,
    defines,
    functions,
    eval_pp_expr
):

    try:

        with open(
            filename,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            text = f.read()

    except FileNotFoundError:

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

    # -----------------------------------------------------
    # Number of braces belonging to namespaces/classes/
    # other non-function scopes.
    # -----------------------------------------------------

    scope_depth = 0

    # -----------------------------------------------------
    # When > 0 we are inside a function body.
    # -----------------------------------------------------

    function_depth = 0

    declaration = ""

    i = 0

    while i < len(lines):
        if(i%100 == 0):
            print(f"Parsing line {i + 1}/{len(lines)} in {filename}", flush=True)

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
        # Ignore inactive preprocessor sections.
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
        # Standalone macro invocation.
        #
        # Example:
        #
        #   REGISTER_CLASS(Foo)
        #
        # Do not mistake it for a function.
        # -------------------------------------------------

        if re.match(
            r'^[A-Z_][A-Z0-9_]*\s*\([^)]*\)\s*$',
            line
        ):

            declaration = ""

            continue

        # -------------------------------------------------
        # Ignore closing namespace/class braces.
        # -------------------------------------------------

        if line.startswith("}"):

            scope_depth = max(
                0,
                scope_depth - 1
            )

            line = re.sub(
                r'^\}\s*while\s*\([^)]*\)\s*',
                '',
                line
            ).strip()

            if not line:

                declaration = ""

                continue

        # -------------------------------------------------
        # Build declaration.
        #
        # C++ declarations commonly span multiple lines.
        # -------------------------------------------------

        if declaration:

            declaration += " "

        declaration += line

        # -------------------------------------------------
        # Look for function body.
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

                # -----------------------------------------
                # Skip function body.
                # -----------------------------------------

                remaining = declaration[
                    brace_position:
                ]

                opens = remaining.count("{")
                closes = remaining.count("}")

                function_depth = (
                    opens - closes
                )

                if function_depth < 0:

                    function_depth = 0

                declaration = ""

                continue

            # -------------------------------------------------
            # Not a function.
            #
            # This can be:
            #
            #   namespace Foo {
            #   class Foo {
            #   struct Foo {
            #   enum Foo {
            #
            # Keep scanning inside the scope.
            # -------------------------------------------------

            opens = declaration.count("{")
            closes = declaration.count("}")

            scope_depth += (
                opens - closes
            )

            if scope_depth < 0:

                scope_depth = 0

            declaration = ""

            continue

        # -------------------------------------------------
        # A semicolon terminates a declaration.
        #
        # This prevents variables/prototypes from leaking
        # into the next line.
        # -------------------------------------------------

        if ";" in line:

            declaration = ""


# =========================================================
# Parse directory with C++ implementations
# =========================================================

def parse_implementations(
    directory,
    defines=None,
    eval_pp_expr=None
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
    # C and C++ implementation extensions.
    # -----------------------------------------------------

    implementation_extensions = {
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".C"
    }

    # -----------------------------------------------------
    # Walk directory tree.
    # -----------------------------------------------------

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

            relative_path = os.path.relpath(
                filename,
                project_root
            )

            if filename in visited:

                continue

            visited.add(filename)

            print(f"Parsing C/C++ file: {filename}", flush=True)

            parse_cpp_file(
                filename,
                relative_path,
                defines,
                functions,
                eval_pp_expr
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
            f"{item['path']:35} "
            f"{item['declaration']}"
        )