# Imports

# Custom modules
import os

from preprocessor import parse_preprocessor, eval_pp_expr
from implementations import (
    parse_implementations,
    print_implementations
)
from compare import (
    compare_prototypes_implementations,
    print_missing,
    print_required_files
)


# Project files
config_txt             = "config.txt"
includes_txt           = "includes.txt"
start_txt              = "start.txt"
prototypes_txt         = "prototypes.txt"
implementations_txt    = "implementations.txt"
lib_txt               = "lib.txt"


# Project values
defines = None
includes = None
prototypes = None
implementations = None


# Main function
def main():

    global defines
    global includes
    global prototypes
    global implementations


    #
    # Read include paths
    #

    try:
        with open(includes_txt, 'r') as file_includes_txt:

            content = file_includes_txt.read()

            print(content)

            includes = [
                line.strip()
                for line in content.split('\n')
                if line.strip()
            ]


    except FileNotFoundError:

        print(f"File '{includes_txt}' not found.")



    #
    # Parse config file
    #

    try:
        with open(config_txt, 'r') as file_config_txt:
            content = file_config_txt.read().strip()
            print(content)
    except FileNotFoundError:
        print(f"File '{config_txt}' not found.")        

    try:
        defines, prototypes = parse_preprocessor(
            content,
            defines=defines,
            include_paths=includes
        )


        print("Defines:")

        for k in sorted(defines):
            print(f"{k} = {defines[k]}")


    except Exception as e:

        print(
            f"Error parsing config file: {config_txt}. "
            f"Error: {e}"
        )


    #
    # Parse start file
    #
    print(f"\nParsing start file: {start_txt}")
    try:
        with open(start_txt, 'r') as file_start_txt:
            content = file_start_txt.read().strip()
            print(content)
    except FileNotFoundError:
        print(f"File '{start_txt}' not found.")  

    try:

        defines, prototypes = parse_preprocessor(
            content,
            defines=defines,
            prototypes=prototypes,
            include_paths=includes
        )


        print("\nDefines:")

        for k in sorted(defines):
            print(f"{k} = {defines[k]}")


    except Exception as e:

        print(
            f"Error parsing start file: {start_txt}. "
            f"Error: {e}"
        )

    #
    # Parse start file, second time, to ensure that all defines are captured
    #
    print(f"\nParsing start file: {start_txt}")
    try:
        with open(start_txt, 'r') as file_start_txt:
            content = file_start_txt.read().strip()
            print(content)
    except FileNotFoundError:
        print(f"File '{start_txt}' not found.")  

    try:

        defines, prototypes = parse_preprocessor(
            content,
            defines=defines,
            prototypes=prototypes,
            include_paths=includes
        )


        print("\nDefines:")

        for k in sorted(defines):
            print(f"{k} = {defines[k]}")


    except Exception as e:

        print(
            f"Error parsing start file: {start_txt}. "
            f"Error: {e}"
        )

    

    #
    # Save prototypes
    #
    print(f"\nSaving prototypes to file: {prototypes_txt}")
    try:

        with open(prototypes_txt, 'w') as file_prototypes_txt:

            for p in prototypes:
                file_prototypes_txt.write(
                    p + "\n"
                )


    except Exception as e:

        print(
            f"Error writing prototypes file. Error: {e}"
        )

    #
    # Parse implementations
    #
    print(f"\nParsing implementations file: {lib_txt}")

    try:
        with open(lib_txt, 'r') as file_lib_txt:
            content = file_lib_txt.read().strip()
            print(content)
    except FileNotFoundError:
        print(f"File '{lib_txt}' not found.")

    implementations = parse_implementations(
        content,
        defines = defines,
        eval_pp_expr = eval_pp_expr,
        verbose=True
    )

    print_implementations(implementations)

    #
    # Save implementations
    #
    print(f"\nSaving implementations to file: {implementations_txt}")

    try:

        with open(implementations_txt, 'w') as file_implementations_txt:

            for p in implementations:
                file_implementations_txt.write(
                    f"{p['name']:35} {p['file']:25} {p['declaration']}\n"
                )


    except Exception as e:

        print(
            f"Error writing implementations file. Error: {e}"
        )

    #
    # Compare prototypes vs implementations
    #

    missing, required_files = compare_prototypes_implementations(
        prototypes,
        implementations
    )


    print_missing(missing)

    print_required_files(required_files)

    #
    # Save missing implementations
    #
    missing_implementations_txt = "missing_implementations.txt"
    print(f"\nSaving missing implementations to file: {missing_implementations_txt}")

    try:

        with open(missing_implementations_txt, 'w') as file_missing_implementations_txt:

            for m in missing:
                file_missing_implementations_txt.write(m + "\n")


    except Exception as e:

        print(
            f"Error writing missing implementations file. Error: {e}"
        )

    #
    # Parse required libs files
    #

    for file in required_files:
        defines, prototypes = parse_preprocessor(
            file,
            defines=defines,
            prototypes=prototypes,
            include_paths=includes
        )

    #
    # Save required files
    #
    required_libs_txt = "required_libs.txt"
    print(f"\nSaving required files to file: {required_libs_txt}")

    try:

        with open(required_libs_txt, 'w') as file_required_libs_txt:

            for r in required_files:
                file_required_libs_txt.write("./" +r + "\n")
    except Exception as e:

        print(
            f"Error writing required files file. Error: {e}"
        )

    #
    # Compare prototypes vs implementations
    #

    missing, required_files = compare_prototypes_implementations(
        prototypes,
        implementations
    )


    print_missing(missing)

    print_required_files(required_files)

if __name__ == '__main__':
    main()