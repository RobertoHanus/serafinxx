import os
import re


# =========================================================
# Extract function name from a C/C++ prototype/declaration
# =========================================================

def extract_function_name(declaration):
    """
    Extract the function name from a C/C++ prototype.

    Examples:

        int Atari800_Initialise(int *argc, char *argv[]);
        -> Atari800_Initialise

        void SaveState::save(size_t);
        -> SaveState::save

        DOS_File & DOS_File::operator=(const DOS_File &);
        -> DOS_File::operator=

        operator bool();
        -> operator bool
    """

    declaration = declaration.strip()

    if not declaration:
        return None

    declaration = declaration.rstrip(";").strip()

    # -----------------------------------------------------
    # Operator overloads
    # -----------------------------------------------------

    match = re.search(
        r'(?:(?:[A-Za-z_]\w*)::)*'
        r'operator\s*'
        r'(?:'
        r'new\[\]|'
        r'delete\[\]|'
        r'new|'
        r'delete|'
        r'<<=|>>=|<<|>>|'
        r'==|!=|<=|>=|'
        r'\+\+|--|&&|\|\||'
        r'->\*|->|'
        r'\+|-|\*|/|%|'
        r'&|\||\^|'
        r'~|!|=|<|>|'
        r'[A-Za-z_]\w*'
        r')',
        declaration
    )

    if match:
        return match.group(0).strip()

    # -----------------------------------------------------
    # Normal qualified function
    # -----------------------------------------------------

    match = re.search(
        r'(?:(?:[A-Za-z_]\w*)::)*'
        r'~?[A-Za-z_]\w*'
        r'\s*\(',
        declaration
    )

    if match:

        name = match.group(0)

        name = name[
            :name.rfind("(")
        ].strip()

        return name

    return None


# =========================================================
# Extract short function name
# =========================================================

def short_function_name(name):

    if not name:
        return None

    name = name.strip()

    if "::" in name:

        return name.rsplit(
            "::",
            1
        )[1].strip()

    return name


# =========================================================
# Normalize function names
# =========================================================

def normalize_function_name(name):

    if not name:
        return None

    name = name.strip()

    # Normalize scope operator

    name = re.sub(
        r'\s*::\s*',
        '::',
        name
    )

    # Normalize operator whitespace

    name = re.sub(
        r'\boperator\s+',
        'operator ',
        name
    )

    # Normalize remaining whitespace

    name = re.sub(
        r'\s+',
        ' ',
        name
    )

    return name.strip()


# =========================================================
# Build implementation index
# =========================================================

def build_implementation_index(implementations):

    exact_index = {}
    short_index = {}

    for impl in implementations:

        name = impl.get(
            "name",
            ""
        )

        if not name:
            continue

        name = normalize_function_name(
            name
        )

        # -------------------------------------------------
        # Exact name
        # -------------------------------------------------

        exact_index.setdefault(
            name,
            []
        ).append(
            impl
        )

        # -------------------------------------------------
        # Short name
        # -------------------------------------------------

        short_name = short_function_name(
            name
        )

        if short_name:

            short_index.setdefault(
                short_name,
                []
            ).append(
                impl
            )

    return (
        exact_index,
        short_index
    )


# =========================================================
# Find implementation
# =========================================================

def find_implementation(
        prototype_name,
        exact_index,
        short_index,
        verbose=False):

    prototype_name = normalize_function_name(
        prototype_name
    )

    # -----------------------------------------------------
    # 1. Exact match
    # -----------------------------------------------------

    exact_matches = exact_index.get(
        prototype_name,
        []
    )

    if exact_matches:

        if verbose:

            print(
                f"DEBUG COMPARE: "
                f"'{prototype_name}' "
                f"EXACT FOUND: True"
            )

        return exact_matches[0]

    # -----------------------------------------------------
    # 2. Short-name match
    # -----------------------------------------------------

    short_name = short_function_name(
        prototype_name
    )

    short_matches = short_index.get(
        short_name,
        []
    )

    # -----------------------------------------------------
    # Unique short-name match
    # -----------------------------------------------------

    if len(short_matches) == 1:

        impl = short_matches[0]

        if verbose:

            print(
                f"DEBUG COMPARE: "
                f"'{prototype_name}' "
                f"SHORT MATCH: "
                f"'{impl.get('name', '')}'"
            )

        return impl

    # -----------------------------------------------------
    # Ambiguous short-name match
    # -----------------------------------------------------

    if len(short_matches) > 1:

        if verbose:

            names = [
                x.get(
                    "name",
                    ""
                )
                for x in short_matches
            ]

            print(
                f"DEBUG COMPARE: "
                f"'{prototype_name}' "
                f"AMBIGUOUS: {names}"
            )

        return None

    # -----------------------------------------------------
    # Not found
    # -----------------------------------------------------

    if verbose:

        print(
            f"DEBUG COMPARE: "
            f"'{prototype_name}' "
            f"FOUND: False"
        )

    return None


# =========================================================
# Compare prototypes against implementations
# =========================================================

def compare_prototypes_implementations(
        prototypes,
        implementations,
        verbose=True):

    # -----------------------------------------------------
    # Build indexes
    # -----------------------------------------------------

    (
        exact_index,
        short_index
    ) = build_implementation_index(
        implementations
    )

    # -----------------------------------------------------
    # Results
    # -----------------------------------------------------

    missing = []

    required_files = set()

    missing_set = set()

    # -----------------------------------------------------
    # Process prototypes
    # -----------------------------------------------------

    for prototype in prototypes:

        name = extract_function_name(
            prototype
        )

        if not name:
            continue

        name = normalize_function_name(
            name
        )

        # -------------------------------------------------
        # Find implementation
        # -------------------------------------------------

        impl = find_implementation(
            name,
            exact_index,
            short_index,
            verbose=verbose
        )

        # -------------------------------------------------
        # Found
        # -------------------------------------------------

        if impl is not None:

            # -------------------------------------------------
            # IMPORTANT:
            #
            # "file" remains the filename only.
            #
            # "path" is the relative path generated by
            # implementations_fast.py.
            #
            # Example:
            #
            # file = cpu.cpp
            # path = dosbox-x/cpu.cpp
            #
            # -------------------------------------------------

            relative_path = impl.get(
                "path"
            )

            if relative_path:

                required_files.add(
                    relative_path
                )

            else:

                # -------------------------------------------------
                # Compatibility with old implementation records
                # that may only contain "file".
                # -------------------------------------------------

                filename = impl.get(
                    "file"
                )

                if filename:

                    required_files.add(
                        filename
                    )

        # -------------------------------------------------
        # Missing
        # -------------------------------------------------

        else:

            if name not in missing_set:

                missing.append(
                    name
                )

                missing_set.add(
                    name
                )

    return (
        missing,
        sorted(required_files)
    )


# =========================================================
# Print missing implementations
# =========================================================

def print_missing(missing):

    print(
        "\nMissing implementations:"
    )

    if not missing:

        print("None")

        return

    for name in sorted(missing):

        print(name)


# =========================================================
# Print required files
# =========================================================

def print_required_files(files):

    print(
        "\nFiles required for prototypes:"
    )

    for path in files:

        print(path)