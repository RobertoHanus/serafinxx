import re


def extract_function_name(declaration):
    """
    Extract function name from a C prototype/declaration.
    """

    declaration = declaration.strip()

    match = re.search(
        r'((?:[A-Za-z_]\w*::)*'
        r'(?:~?[A-Za-z_]\w*|'
        r'operator\s*(?:[^\s(]+)))'
        r'\s*\(',
        declaration
    )

    if match:
        return match.group(1)

    return None



def compare_prototypes_implementations(
        prototypes,
        implementations
    ):

    #
    # Build implementation index
    #

    impl_index = {}

    for impl in implementations:

        name = impl["name"]

        impl_index[name] = impl



    #
    # Search missing implementations
    #

    missing = []

    required_files = set()


    for prototype in prototypes:

        name = extract_function_name(prototype)

        if not name:
            continue

        """
        print(
            "DEBUG COMPARE:",
            repr(name),
            "FOUND:",
            name in impl_index
        )

        if name not in impl_index:

            print(
                "DEBUG IMPLEMENTATION NAMES:",
                [
                    repr(k)
                    for k in impl_index
                    if "InvalidateCachedHandlers" in k
                ]
            )
            exit()
        """

        if name in impl_index:

            required_files.add(
                impl_index[name]["path"]
            )

        else:

            missing.append(
                name
            )


    return (
        missing,
        sorted(required_files)
    )



def print_missing(missing):

    print("\nMissing implementations:")

    if not missing:
        print("None")
        return

    for m in sorted(missing):
        print(m)



def print_required_files(files):

    print("\nFiles required for prototypes:")

    for f in files:
        print(f)