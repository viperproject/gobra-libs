"""Module for profiling Viper and Gobra programs using Silicon and Z3's quantifier instantiation profiling."""

import argparse
import csv
import logging
import os
import time
import subprocess

from util import file_path


def main():
    """Main function of the profiler."""
    # Set up logging.
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()

    metadata = generate_metadata(args)

    # Set Z3 environment for Gobra and Silicon.
    os.environ["Z3_EXE"] = str(args.z3_path)

    # Generate Gobra file if needed.
    if args.program_path.suffix == '.gobra':
        if args.gobra_path is None:
            logging.error("Path to Gobra jar is required for Gobra files.")
            raise ValueError("Path to Gobra jar is required for Gobra files.")

        # TODO Refactor this so we can pass it using shell=False
        command = f"java -jar -Xss128m {args.gobra_path} --printVpr --noVerify -i {args.program_path}"

        logging.info("Generating Viper file.")
        time_checked_command(command, shell=True)
        logging.info("Viper file generated.")

        vpr_file_path = args.program_path.with_suffix(".gobra.vpr")
    # Due to program_path(), this is a Viper file.
    else:
        vpr_file_path = args.program_path

    data = []
    for i in range(0, args.iterations):
        # --useOldAxiomatization: At the time of writing, the new axiomatization has anonymous axioms, which is why
        # we use the old one with names.
        command = [args.silicon_path, "--useOldAxiomatization", "--numberOfParallelVerifiers", "1", "--z3Args",
                   f'smt.qi.profile=true smt.qi.profile_freq={args.granularity}', vpr_file_path]
        if args.z3RandomizeSeeds:
            command.append("--z3RandomizeSeeds")
        if args.disableSetAxiomatization:
            # Get current directory of this file.
            script_dir = os.path.dirname(os.path.abspath(__file__))
            command.append("--setAxiomatizationFile")
            command.append(os.path.join(script_dir, 'noaxioms_sets.vpr'))

        logging.info(f"Running Silicon with profiling. Iteration: {i + 1} of {args.iterations}.")
        command, execution_time = time_checked_command(command)
        logging.info(f"Silicon finished in {execution_time} seconds.")

        logging.info("Processing Silicon's profiling output")
        data_point = process_output(command.stdout)
        logging.info("Silicon's profiling output processed.")
        data_point["execution_time"] = execution_time

        data.append(data_point)

    # Write CSV files.
    csv_path = (metadata["program_path"].parent / format_metadata(metadata)).with_suffix(".csv")
    write_to_csv(data, csv_path)


def process_output(output):
    """Process the data from Silicon's output.

    When we profile Silicon, based on the granularity, a quantifier instantiation may trigger the printing of how often
    that quantifier has been instantiated up until now. This function processes that output and returns a dictionary
    which maps quantifier names to the latest number of instantiations.
    """
    # Drop Silicon's preamble and epilogue.
    output = output.splitlines()
    output = output[1:-1]

    # Keeps track of current number of quantifier instantiations.
    result = {}

    # Process the output.
    # Example of rows we are processing:
    # [quantifier_instances] $Multiset[Int]_prog.card_non_negative :   2500 :  10 : 11
    for line in output:
        columns = [column.strip() for column in line.split(":")]

        # We don't want to include "[quantifier_instances] " in the name.
        name = columns[0].removeprefix("[quantifier_instances]").strip()
        instantiations = int(columns[1])

        # We prefix the name with "qi-" to indicate that it is a quantifier instantiation to avoid potential name
        # clashes with execution_time.
        result[f"qi-{name}"] = instantiations

    return result


def time_checked_command(command, shell=False):
    """Runs a command and returns its runtime and its results.

    This function is a wrapper around subprocess.run. It measures the runtime and checks whether the command was
    successful. If it wasn't, it prints all the information and raises RuntimeError.
    """
    logging.debug(f"Running {command}")
    try:
        start_time = time.time()
        command = subprocess.run(command, capture_output=True, text=True, check=True, shell=shell)
        end_time = time.time()
        execution_time = end_time - start_time
        logging.debug(f"Command finished in {execution_time} seconds.")
        return command, execution_time
    except subprocess.CalledProcessError as e:
        logging.error(f"Command {e.cmd} failed with return code {e.returncode}.")
        logging.error(f"stdout: {e.stdout}")
        logging.error(f"stderr: {e.stderr}")
        raise RuntimeError(f"Command {e.cmd} failed with return code {e.returncode}.")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("program_path", type=program_path,
                        help="Gobra or Viper program to be profiled")
    parser.add_argument("--silicon_path", type=file_path, required=True,
                        help="path to silicon.sh")
    parser.add_argument("--z3_path", type=file_path, required=True,
                        help="path to Z3 binary")
    parser.add_argument("--gobra_path", type=file_path, required=False,
                        help="path to Gobra jar")
    parser.add_argument("--iterations", type=positive, required=False, default=1,
                        help="number of times profiling is repeated")
    parser.add_argument("--granularity", type=positive, required=False, default=1,
                        help="granularity of quantifier reporting")
    parser.add_argument("--z3RandomizeSeeds", action="store_true", required=False,
                        help=("set various Z3 random seeds to random values. Note that "
                              "profiling may be non-deterministic even if this setting "
                              "is set to False."))
    parser.add_argument("--disableSetAxiomatization", action="store_true", required=False,
                        help="disable the axiomatization of set operations.")
    return parser.parse_args()


def generate_metadata(args):
    """Generate metadata for the CSV file."""
    logging.info("Generating metadata.")
    metadata = {"program_path": args.program_path}
    logging.info(f"Program path: {metadata['program_path']}")

    logging.info("Getting version of Silicon.")
    command = [args.silicon_path]
    logging.debug(f"Running {command}")
    # This shouldn't be checked, as Silicon will return a non-zero exit code (no option for version).
    command_stdout = subprocess.run(command, capture_output=True, text=True).stdout
    # Convert
    # Silicon 1.1-SNAPSHOT (7fea2aa7+)
    #   Command-line interface: Required option 'file' not found.
    # Run with just --help for usage and options
    # to
    # 7fea2aa7
    metadata["silicon_version"] = command_stdout.splitlines()[0].split()[-1][1:-2]
    logging.info(f"Silicon version: {metadata['silicon_version']}")

    logging.info("Getting version of Z3.")
    command = [args.z3_path, "-version"]
    command, _ = time_checked_command(command)
    # Convert "Z3 version 4.8.7 - 64 bit" to "4_8_7".
    metadata["z3_version"] = command.stdout.split()[2].replace('.', '_')
    logging.info(f"Z3 version: {metadata['z3_version']}")

    # Get version of Gobra if applicable.
    if args.gobra_path is not None:
        logging.info("Getting version of Gobra.")
        # TODO Refactor this so we can pass it using shell=False
        command = f"java -jar {args.gobra_path} --version"
        command, _ = time_checked_command(command, shell=True)
        # Convert
        #
        #  Gobra (c) Copyright ETH Zurich 2012 - 2022
        #    version 1.1-SNAPSHOT (529d2a49@(detached))
        #
        # to
        # 529d2a49
        metadata["gobra_version"] = command.stdout.splitlines()[2].split()[-1].partition("@")[0][1:]
        logging.info(f"Gobra version: {metadata['gobra_version']}")
    else:
        logging.info("Getting Gobra version not required. Continuing.")

    metadata["iterations"] = args.iterations
    logging.info(f"Iterations: {metadata['iterations']}")

    metadata["granularity"] = args.granularity
    logging.info(f"Granularity: {metadata['granularity']}")
    metadata["z3RandomizeSeeds"] = args.z3RandomizeSeeds
    logging.info(f"Z3 randomize seeds: {metadata['z3RandomizeSeeds']}")
    metadata["disableSetAxiomatization"] = args.disableSetAxiomatization
    logging.info(f"Disable set axiomatization: {metadata['disableSetAxiomatization']}")

    logging.info("Metadata generated.")
    return metadata


def format_metadata(metadata):
    """Format the metadata into a single string.

    This string is used as the filename of the CSV file.
    """
    result = f'{metadata["program_path"].stem.replace(".", "_")}'
    if metadata["z3RandomizeSeeds"]:
        result += "-rand"
    if metadata["disableSetAxiomatization"]:
        result += "-no_set_axiom"
    result += f'-iter_{metadata["iterations"]}'
    result += f'-gran_{metadata["granularity"]}'
    result += f'-sil_ver_{metadata["silicon_version"]}'
    result += f'-z3_ver_{metadata["z3_version"]}'
    if "gobra_version" in metadata:
        result += f'-gobra_ver_{metadata["gobra_version"]}'

    return result


def write_to_csv(data, csv_path):
    """Write the data to a CSV file."""
    logging.info(f"Writing {csv_path}.")
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()

        for data_point in data:
            writer.writerow(data_point)

    logging.info(f"Data written to {csv_path}.")


def program_path(string):
    """Checks that the string is a valid path to either a Viper or Gobra program."""
    path = file_path(string)
    if path.suffix not in [".gobra", ".vpr"]:
        raise argparse.ArgumentTypeError(f"Wrong suffix: {path} is not a valid path to a program")

    # TODO Check whether this workaround is a bug in Gobra that we need to report
    if not path.is_absolute():
        path = path.resolve()

    return path


def positive(string):
    """Checks that the string is a positive integer."""
    value = int(string)
    if value <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not larger or equal to 1")
    return value


if __name__ == "__main__":
    main()
